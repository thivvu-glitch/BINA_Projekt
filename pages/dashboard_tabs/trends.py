import streamlit as st
import pandas as pd
import plotly.express as px
import random
from utils.data_loader import load_tournament_players

def render(df, filtered_df, players_info_df, selected_leagues, TOURNAMENT_OPTIONS, season_options):
    st.header("📈 Zeitvergleich & Trends")
    st.markdown("""
    **Welche Fragen werden dir in diesem Register beantwortet?**
    - Wie entwickeln sich Verletzungen und Ausfalltage über mehrere Saisons hinweg?
    - Welche Auswirkungen haben internationale Turniere wie WM oder EM auf das Verletzungsrisiko?
    - Welche Ligen oder Saisons weisen die höchsten Verletzungszahlen und längsten Ausfallzeiten auf?
                
    **Für wen?**                
    * Sportdirektoren
    * Trainer
    * medizinische Abteilungen

    **Was sieht man?**
    - **Verletzungsverlauf:** Entwicklung der Verletzungsfälle und Ausfalltage pro Saison
    - **Turnier-Auswirkungen:** Vergleich Grossturniere (WM/EM) vs. reguläre Saisons
    - **Trend-Analyse:** Identifikation von saisonalen Mustern und Belastungsspitzen
    - **Ressourcenplanung:** Datenbasierte Prognosen für Kader-Management und medizinische Kapazitäten
    """)
    st.divider()
    
    # --- New Comparison Logic ---
    st.subheader("📊 Individueller Kohorten-Vergleich (Turniere, Ligen & Saisons)")
    st.markdown("Erstelle zwei individuelle Spielergruppen (Kohorten), um deren Verletzungsmuster direkt miteinander zu vergleichen. Dies ermöglicht die Analyse von Turnier-Belastungen als auch direkte Vergleiche zwischen Ligen oder Saisons.")
    
    st.info("""
    **Anleitung zur Konfiguration der Analyse-Gruppen:**
    * **Turnier-Analyse:** Wähle in Kohorte A ein Turnier (z. B. WM 2022) und in Kohorte B 'Keine Turnierteilnahme'. Aktiviere das 'Stratified Matching', um eine statistisch faire Vergleichsgruppe (gleiche Ligen & Positionen) zu generieren.
    * **Ligen- oder Saison-Vergleich:** Wähle bei beiden Kohorten im Turnierfilter **'Alle Spieler'**. Konfiguriere dann die Ligen und Saisons nach Belieben (z. B. Kohorte A: Premier League, Kohorte B: Bundesliga). *Wichtig: Deaktiviere in diesem Fall das 'Stratified Matching', da du alle Spieler der gewählten Liga sehen willst.*
    """, icon="💡")
    
    st.markdown("#### ⚙️ Setup für Kohorten-Vergleich")
    with st.container():
        c1, c2 = st.columns(2)
        
        league_options_all = sorted(df['league'].dropna().unique().tolist())
        
        with c1:
            st.markdown("**1. Analyse-Kohorte A (Fokusgruppe)**")
            v_tournament = st.selectbox(
                "Turnierfilter (A)",
                options=TOURNAMENT_OPTIONS,
                index=2, # Default to WM
                key="v_group_tournament"
            )
            v_leagues = st.multiselect("Ligen (A)", league_options_all, default=league_options_all, key="v_group_leagues")
            v_season = st.multiselect("Saison (A)", season_options, default=season_options, key="v_group_season")
            
        with c2:
            st.markdown("**2. Analyse-Kohorte B (Vergleichsgruppe)**")
            k_tournament = st.selectbox(
                "Turnierfilter (B)",
                options=TOURNAMENT_OPTIONS,
                index=5, # Default to Keine Turnierteilnahme
                key="k_group_tournament"
            )
            k_leagues = st.multiselect("Ligen (B)", league_options_all, default=league_options_all, key="k_group_leagues")
            k_season = st.multiselect("Saison (B)", season_options, default=season_options, key="k_group_season")

        st.markdown("---")
        c_chk, c_btn = st.columns([3, 1])
        with c_chk:
            use_randomizer = st.checkbox(
                "🎲 Äquivalenzgruppe (Stratified Matching): Kontrollgruppe B an Liga und Position von Gruppe A spiegeln", 
                value=True,
                help="Zieht für Gruppe B exakt dieselbe Anzahl an Spielern mit der gleichen Ligen- und Positions-Verteilung wie in Gruppe A."
            )
        btn_placeholder = c_btn.empty()

    # Helper function to get the base players
    def get_tournament_players(t_filter, all_players):
        if "Alle Spieler" in t_filter:
            return set(all_players)
        e20, w22, e24 = load_tournament_players()
        if "EURO 2020" in t_filter:
            return e20.intersection(all_players)
        elif "WM 2022" in t_filter:
            return w22.intersection(all_players)
        elif "EURO 2024" in t_filter:
            return e24.intersection(all_players)
        elif "WM und EM" in t_filter:
            return e20.union(w22).union(e24).intersection(all_players)
        elif "Keine Turnierteilnahme" in t_filter:
            all_t = e20.union(w22).union(e24)
            return set(all_players) - all_t
        return set(all_players)

    all_players_base = players_info_df['player_id'].dropna().astype(int).unique()
    
    players_a = list(get_tournament_players(v_tournament, all_players_base))
    players_b_pool = list(get_tournament_players(k_tournament, all_players_base))
    players_b = players_b_pool.copy()

    # Apply Stratified Matching Randomizer (MV Focus, without Age)
    n_a = len(players_a)
    exact_match_count = 0
    fallback_1_count = 0
    
    if use_randomizer and n_a > 0:
        if len(players_b_pool) > n_a:
            seed_str = f"{v_tournament}_{k_tournament}_{''.join(v_season)}_{''.join(k_season)}"
            random.seed(hash(seed_str))
            
            # DataFrame representation for Stratified Sampling
            df_a_info = players_info_df[players_info_df['player_id'].isin(players_a)].copy()
            df_b_info = players_info_df[players_info_df['player_id'].isin(players_b_pool)].copy()
            
            # Remove duplicate names to ensure exact counts
            df_a_info = df_a_info.drop_duplicates(subset=['player_id'])
            df_b_info = df_b_info.drop_duplicates(subset=['player_id'])
            
            # Fill NA to avoid grouping issues
            df_a_info['current_club_domestic_competition_id'] = df_a_info['current_club_domestic_competition_id'].fillna('Unknown')
            df_a_info['position'] = df_a_info['position'].fillna('Unknown')
            df_b_info['current_club_domestic_competition_id'] = df_b_info['current_club_domestic_competition_id'].fillna('Unknown')
            df_b_info['position'] = df_b_info['position'].fillna('Unknown')
            
            def get_mv_tier(val):
                if pd.isna(val): return 'Unknown'
                if val >= 40000000: return 'Tier 1 (>40M)'
                elif val >= 10000000: return 'Tier 2 (10M-40M)'
                else: return 'Tier 3 (<10M)'

            df_a_info['mv_tier'] = df_a_info['market_value_in_eur'].apply(get_mv_tier)
            df_b_info['mv_tier'] = df_b_info['market_value_in_eur'].apply(get_mv_tier)
            
            # Strata definieren (Liga + Position + Marktwert-Tier) - OHNE Alter
            strata_counts = df_a_info.groupby(['current_club_domestic_competition_id', 'position', 'mv_tier']).size().to_dict()
            
            sampled_b_ids = []
            
            for (league, pos, mv_tier), count in strata_counts.items():
                # Versuch 1: Exaktes Match (Liga + Position + MV-Tier)
                exact_pool = df_b_info[
                    (df_b_info['current_club_domestic_competition_id'] == league) & 
                    (df_b_info['position'] == pos) & 
                    (df_b_info['mv_tier'] == mv_tier)
                ]['player_id'].tolist()
                
                if len(exact_pool) >= count:
                    sampled_b_ids.extend(random.sample(exact_pool, count))
                    exact_match_count += count
                else:
                    sampled_b_ids.extend(exact_pool)
                    exact_match_count += len(exact_pool)
                    needed_more = count - len(exact_pool)
                    
                    # Fallback 1: Nur Liga und Position gleich (Marktwert egal)
                    fallback_1_pool = df_b_info[
                        (df_b_info['current_club_domestic_competition_id'] == league) & 
                        (df_b_info['position'] == pos)
                    ]['player_id'].tolist()
                    
                    available_f1 = list(set(fallback_1_pool) - set(exact_pool))
                    
                    if len(available_f1) >= needed_more:
                        sampled_b_ids.extend(random.sample(available_f1, needed_more))
                        fallback_1_count += needed_more
                    else:
                        sampled_b_ids.extend(available_f1)
                        fallback_1_count += len(available_f1)
            
            # Fallback 2: Globale Auffüllung falls noch Spieler fehlen, um exakt n_a zu erreichen
            remaining_needed = n_a - len(sampled_b_ids)
            if remaining_needed > 0:
                remaining_pool = list(set(players_b_pool) - set(sampled_b_ids))
                if len(remaining_pool) >= remaining_needed:
                    sampled_b_ids.extend(random.sample(remaining_pool, remaining_needed))
                else:
                    sampled_b_ids.extend(remaining_pool)
                    
            players_b = sampled_b_ids

    with btn_placeholder:
        with st.popover("👥 Spielerlisten anzeigen", use_container_width=True):
            st.markdown("**Gegenüberstellung: Fokus vs. Ersatz (Stratified nach Marktwert)**")
            
            total_b = len(players_b)
            if total_b > 0 and use_randomizer:
                exact_pct = int((exact_match_count / total_b) * 100)
                f1_pct = int((fallback_1_count / total_b) * 100)
                st.info(f"**Matching-Qualität:** {exact_pct}% Exakter Ersatz (Gleiche Liga, Position & Marktwert-Klasse), {f1_pct}% Fallback (Nur gleiche Liga & Position).", icon="ℹ️")

            df_a_show = players_info_df[players_info_df['player_id'].isin(players_a)][['player_id', 'name', 'market_value_in_eur']].drop_duplicates('player_id')
            df_b_show = players_info_df[players_info_df['player_id'].isin(players_b)][['player_id', 'name', 'market_value_in_eur']].drop_duplicates('player_id')
            
            df_a_show = df_a_show.sort_values(by='market_value_in_eur', ascending=False, na_position='last').reset_index(drop=True)
            df_b_show = df_b_show.sort_values(by='market_value_in_eur', ascending=False, na_position='last').reset_index(drop=True)
            
            max_len = max(len(df_a_show), len(df_b_show))
            if max_len > 0:
                a_names = df_a_show['name'].tolist() + ["-"] * (max_len - len(df_a_show))
                a_mw = df_a_show['market_value_in_eur'].tolist() + [pd.NA] * (max_len - len(df_a_show))
                
                b_names = df_b_show['name'].tolist() + ["-"] * (max_len - len(df_b_show))
                b_mw = df_b_show['market_value_in_eur'].tolist() + [pd.NA] * (max_len - len(df_b_show))
                
                def fmt_mw(x): return f"{x/1000000:.1f} Mio. €" if pd.notna(x) else "-"
                
                final_df = pd.DataFrame({
                    'Nr.': range(1, max_len + 1),
                    'Spieler (A)': a_names,
                    'Marktwert (A)': [fmt_mw(x) for x in a_mw],
                    'Ersatz-Spieler (B)': b_names,
                    'Marktwert (B)': [fmt_mw(x) for x in b_mw]
                })
                
                st.dataframe(final_df, hide_index=True, use_container_width=True)
            else:
                st.info("Keine Spieler in den gewählten Kohorten vorhanden.")

    # Construct Comparison Data (Filtering the injuries dataframe based on the player populations)
    df_a = df[df['player_id'].isin(players_a)].copy()
    if v_leagues: df_a = df_a[df_a['league'].isin(v_leagues)]
    if v_season: df_a = df_a[df_a['Season'].isin(v_season)]
    league_str_a = f" ({', '.join(v_leagues)})" if v_leagues and len(v_leagues) < len(league_options_all) else ""
    df_a['Label'] = f"A: {v_tournament.split(' (')[0]}{league_str_a}"
    
    df_b = df[df['player_id'].isin(players_b)].copy()
    if k_leagues: df_b = df_b[df_b['league'].isin(k_leagues)]
    if k_season: df_b = df_b[df_b['Season'].isin(k_season)]
    
    league_str_b = f" ({', '.join(k_leagues)})" if k_leagues and len(k_leagues) < len(league_options_all) else ""
    df_b['Label'] = f"B: {k_tournament.split(' (')[0]}{league_str_b}"
    
    # Show Summary Metrics
    c_m1, c_m2 = st.columns(2)
    c_m1.metric(f"Gruppe A: Spielerbasis", f"{len(players_a)} Spieler", f"-> {len(df_a)} Verletzungen", delta_color="off")
    c_m2.metric(f"Gruppe B: Spielerbasis", f"{len(players_b)} Spieler", f"-> {len(df_b)} Verletzungen", delta_color="off")

    compare_df = pd.concat([df_a, df_b])
    color_map = {df_a['Label'].iloc[0]: "red", df_b['Label'].iloc[0]: "blue"} if not compare_df.empty else {}
    
    if not compare_df.empty:
        # Create a continuous Year-Month timeline
        compare_df['YearMonth'] = compare_df['injury_from_parsed'].dt.to_period('M').dt.to_timestamp()
        monthly = compare_df.groupby(['YearMonth', 'Label']).size().reset_index(name='Anzahl')
        monthly = monthly.sort_values(['YearMonth'])
        
        fig_month = px.line(
            monthly,
            x='YearMonth',
            y='Anzahl',
            color='Label',
            color_discrete_map=color_map,
            markers=True,
            title="Verletzungen im zeitlichen Verlauf (Vergleich)",
            labels={'YearMonth': 'Zeitpunkt', 'Anzahl': 'Anzahl Verletzungen', 'Label': 'Auswahl'}
        )
        min_date = monthly['YearMonth'].min()
        max_date = monthly['YearMonth'].max()
        
        # Determine X-Axis default view range
        season_start_year = min_date.year if min_date.month >= 8 else min_date.year - 1
        view_start = pd.to_datetime(f"{season_start_year}-08-01")
        
        if "WM 2022" in v_tournament:
            t_start = pd.to_datetime("2022-11-01")
            if t_start <= max_date: view_start = t_start
        elif "EURO 2020" in v_tournament:
            t_start = pd.to_datetime("2021-06-01")
            if t_start <= max_date: view_start = t_start
        elif "EURO 2024" in v_tournament:
            t_start = pd.to_datetime("2024-06-01")
            if t_start <= max_date: view_start = t_start
            
        view_end = max_date + pd.DateOffset(months=1)
        
        fig_month.update_xaxes(
            tickformat="%b %Y", 
            range=[view_start.strftime("%Y-%m-%d"), view_end.strftime("%Y-%m-%d")]
        )
        
        # Add VRECT for Tournament Duration using actual dates, only if within selected data range
        
        if "WM 2022" in v_tournament:
            t_start, t_end = pd.to_datetime("2022-11-01"), pd.to_datetime("2022-12-31")
            if (t_start <= max_date) and (t_end >= min_date):
                fig_month.add_vrect(x0="2022-11-01", x1="2022-12-31", fillcolor="yellow", opacity=0.3, line_width=0, annotation_text="WM 2022")
        elif "EURO 2020" in v_tournament:
            t_start, t_end = pd.to_datetime("2021-06-01"), pd.to_datetime("2021-07-31")
            if (t_start <= max_date) and (t_end >= min_date):
                fig_month.add_vrect(x0="2021-06-01", x1="2021-07-31", fillcolor="blue", opacity=0.3, line_width=0, annotation_text="EURO 2020")
        elif "EURO 2024" in v_tournament:
            t_start, t_end = pd.to_datetime("2024-06-01"), pd.to_datetime("2024-07-31")
            if (t_start <= max_date) and (t_end >= min_date):
                fig_month.add_vrect(x0="2024-06-01", x1="2024-07-31", fillcolor="green", opacity=0.3, line_width=0, annotation_text="EURO 2024")

        st.plotly_chart(fig_month, use_container_width=True)
    else:
        st.info("Keine Daten für diesen Vergleich verfügbar.")

    st.markdown("#### 📆 Verletzungsentwicklung über die Saisons")
    st.markdown("Diese Grafiken zeigen die zeitliche Entwicklung über die verfügbaren Saisons. Im ersten Diagramm ist die **absolute Anzahl der Verletzungen** pro Saison und Liga dargestellt. Im zweiten Diagramm sehen Sie die **gesamten Ausfalltage**, die durch diese Verletzungen verursacht wurden. So lässt sich nicht nur erkennen, ob Verletzungen häufiger geworden sind, sondern auch, ob deren Schweregrad (anhand der Ausfalltage) zu- oder abgenommen hat.")
    
    season_counts = compare_df.groupby(['Season', 'Label']).size().reset_index(name='Anzahl')
    if not season_counts.empty:
        # Sortieren für chronologische Differenz-Berechnung
        season_counts = season_counts.sort_values(['Label', 'Season'])
        season_counts['Diff'] = season_counts.groupby('Label')['Anzahl'].diff()
        
        def format_diff(val):
            if pd.isna(val):
                return ""
            elif val > 0:
                return f"<br>(+{int(val)})"
            elif val < 0:
                return f"<br>({int(val)})"
            else:
                return "<br>(±0)"
                
        season_counts['Text'] = season_counts['Anzahl'].astype(str) + season_counts['Diff'].apply(format_diff)

        st.markdown("**1. Anzahl der Verletzungen pro Saison** *(Zahl = Gesamtwert, in Klammern = Veränderung zur Vorsaison)*")
        fig_season = px.bar(
            season_counts,
            x='Season',
            y='Anzahl',
            color='Label',
            color_discrete_map=color_map,
            barmode='group',
            text='Text',
            labels={'Season': 'Saison', 'Anzahl': 'Anzahl Verletzungen', 'Label': 'Gruppe'}
        )
        fig_season.update_traces(textposition='outside', textfont_size=11)
        fig_season.update_layout(margin=dict(t=50))
        st.plotly_chart(fig_season, use_container_width=True)
        
        st.markdown("**2. Gesamte Ausfalltage pro Saison** *(Zahl = Gesamtwert, in Klammern = Veränderung zur Vorsaison)*")
        season_days = compare_df.groupby(['Season', 'Label'])['Days'].sum().reset_index(name='Ausfalltage')
        season_days = season_days.sort_values(['Label', 'Season'])
        season_days['Diff'] = season_days.groupby('Label')['Ausfalltage'].diff()
        season_days['Text'] = season_days['Ausfalltage'].astype(int).astype(str) + season_days['Diff'].apply(format_diff)
        
        fig_days = px.bar(
            season_days,
            x='Season',
            y='Ausfalltage',
            color='Label',
            color_discrete_map=color_map,
            barmode='group',
            text='Text',
            labels={'Season': 'Saison', 'Ausfalltage': 'Gesamte Ausfalltage', 'Label': 'Gruppe'}
        )
        fig_days.update_traces(textposition='outside', textfont_size=11)
        fig_days.update_layout(margin=dict(t=50))
        st.plotly_chart(fig_days, use_container_width=True)
    else:
        st.info("Keine Daten für diesen Vergleich verfügbar.")

    st.subheader("🔎 Fazit zum Ligenvergleich")
    if len(selected_leagues) >= 2 and not filtered_df.empty:
        most_injuries_league = filtered_df['league'].value_counts().idxmax()
        most_severe_league = filtered_df.groupby('league')['Days'].mean().idxmax()

        monthly_peak = filtered_df.groupby(['league', 'Month'])['Days'].count().reset_index()
        monthly_peak.columns = ['league', 'Month', 'Count']
        monthly_peak = monthly_peak.loc[monthly_peak.groupby('league')['Count'].idxmax()]

        fazit_text = f"**Vergleich der ausgewählten Ligen ({', '.join(selected_leagues)}):**\\n\\n"
        fazit_text += f"- **Häufigkeit:** Die absolute Mehrheit der Verletzungen weist die **{most_injuries_league}** auf.\\n"
        fazit_text += f"- **Schweregrad:** Die längsten durchschnittlichen Ausfallzeiten gibt es in der **{most_severe_league}**.\\n"
        fazit_text += "- **Saisonale Spitzen (Wann steigen die Verletzungen?):**\\n"

        for _, row in monthly_peak.iterrows():
            fazit_text += f"  - In der **{row['league']}** gibt es den höchsten Anstieg an Verletzungen im **{row['Month']}**.\\n"

        st.info(fazit_text)
    elif len(selected_leagues) < 2:
        st.info("Wähle in der Seitenleiste mindestens zwei Ligen aus, um ein automatisches Vergleichs-Fazit zu generieren.")
    else:
        st.info("Keine Daten für ein Fazit vorhanden.")
