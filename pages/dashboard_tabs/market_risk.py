import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.helpers import get_injury_color, calculate_contract_risk

def render(df, filtered_df, val_df, players_info_df, player_options_map):

    st.header("💸 Marktwert-Impact: Verletzungen & Finanzen")
    st.markdown("""
    **Welche Fragen werden dir in diesem Register beantwortet?**                
    - Wie haben sich Verletzungen auf den Marktwert eines Spielers ausgewirkt?
    - Welche Verletzung hatte den grössten finanziellen Impact auf einen Spieler?
    - Wie entwickelte sich der Marktwert vor, während und nach einer Verletzung?
    - Wie hoch ist das finanzielle Risiko bei einer Vertragsverlängerung oder Neuverpflichtung?
    - Wie lange fallen Spieler im Durchschnitt bei bestimmten Verletzungen aus?
                    
    **Für wen?**
    - Sportdirektor
    - Scouts
    - Vertragsverhandler
                
    **Was sieht man?**
    - **Spieler Steckbrief:** Spielerprofil, aktueller Verein, Marktwert
    - **Marktwertverlauf:** Verlauf des Marktwerts über die Zeit, mit Fokus auf Verletzungsphasen
    - **Fokus schwerste Verletzung:** Detaillierte Analyse der schwersten Verletzung und deren Einfluss auf den Marktwert
    - **Verletzungsübersicht:** Alle Verletzungen des Spielers und deren Impact auf den Marktwert
    - **Vertragsrisikoanalyse:** Basierend auf durchschnittlicher Verletzungsdauer und Marktwert eine Einschätzung des finanziellen Risikos und konkrete Empfehlung
    """)
    st.divider()
    
    st.info("""
    **So nutzt du die Suche:**
    1. **Spieler analysieren:** Suche links nach einem Spieler (z. B. Neymar). Du siehst sofort seinen Marktwertverlauf.
    2. **Verletzung isolieren:** Wähle rechts im Dropdown eine seiner spezifischen Verletzungen aus. Das System blendet dann nur diese Verletzung im Chart ein, damit du exakt den Marktwert-Drop nach dieser Phase studieren kannst.
    3. **Katalog durchsuchen:** Wenn kein Spieler gewählt ist, kannst du rechts nach einer bestimmten Verletzung suchen, um alle betroffenen Spieler im Katalog anzuzeigen.
    """, icon="💡")
    st.divider()
    
    # --- New Unified Search Area ---
    st.subheader("🔍 Suche & Analyse")
    sc1, sc2 = st.columns(2)
    if 'risk_selected_player' not in st.session_state:
        st.session_state['risk_selected_player'] = None

    with sc1:
        player_options_local = sorted(player_options_map.keys())
        
        def on_player_select():
            """Callback: Aktualisiert Session State nur wenn Widget sich ändert"""
            selection = st.session_state.player_search_widget
            st.session_state['risk_selected_player'] = selection[0] if selection else None
        
        st.multiselect(
            "👤 Spieler suchen",
            options=player_options_local,
            default=[st.session_state['risk_selected_player']] if st.session_state['risk_selected_player'] in player_options_local else [],
            max_selections=1,
            help="Wähle einen Spieler aus, um seinen detaillierten Steckbrief zu sehen.",
            key='player_search_widget',  # ← Widget-Key für Session State
            on_change=on_player_select   # ← Callback nur bei echten Änderungen
        )
        
    with sc2:
        current_p = st.session_state['risk_selected_player']
        if current_p:
            selected_pid = player_options_map.get(current_p)
            p_injuries = df[df['player_id'] == selected_pid]
            available_injuries = sorted(p_injuries['Injury'].dropna().unique().tolist())
            help_text = "Filtere die Ansicht im Chart auf eine bestimmte Verletzung dieses Spielers."
        else:
            available_injuries = sorted(df['Injury'].dropna().unique().tolist())
            help_text = "Filtere den Katalog nach einer bestimmten Verletzungsart."
            
        injury_options = ["Alle Verletzungen"] + available_injuries
        selected_injury_risk = st.selectbox(
            "🩹 Verletzung suchen",
            options=injury_options,
            index=0,
            help=help_text
        )

    st.divider()

    if st.session_state['risk_selected_player']:
        p_name = st.session_state['risk_selected_player']
        selected_pid = player_options_map.get(p_name)
        
        # Back Button
        if st.button("⬅️ Zurück zum Katalog"):
            st.session_state['risk_selected_player'] = None
            st.rerun()

        # 1. Fetch player details for the "Steckbrief"
        p_info = players_info_df[players_info_df['player_id'] == selected_pid]
        
        if not p_info.empty:
            p_data = p_info.iloc[0]
            
            # --- Spieler-Steckbrief Layout ---
            st.markdown(f"### 👤 Spieler-Steckbrief: {p_data['name']}")
            
            prof_col1, prof_col2 = st.columns([0.8, 3.2])
            
            with prof_col1:
                # Display player image
                if pd.notna(p_data['image_url']):
                    st.image(p_data['image_url'], use_container_width=True)
                else:
                    st.info("Kein Bild verfügbar")
            
            with prof_col2:
                # Display biographical data in columns
                stat_col1, stat_col2 = st.columns(2)
                
                with stat_col1:
                    st.write(f"**Nationalität:** {p_data['country_of_citizenship']}")
                    st.write(f"**Geburtsdatum:** {pd.to_datetime(p_data['date_of_birth']).strftime('%d.%m.%Y') if pd.notna(p_data['date_of_birth']) else 'Unbekannt'}")
                    st.write(f"**Position:** {p_data['position']}")
                    st.write(f"**Starker Fuss:** {p_data['foot'].capitalize() if pd.notna(p_data['foot']) else 'Unbekannt'}")
                    
                    # Current Club moved here (directly under Starker Fuss)
                    c_name = p_data['current_club_name']
                    c_id = p_data['current_club_id']
                    if pd.notna(c_id):
                        logo_url = f"https://tmssl.akamaized.net/images/wappen/medium/{int(c_id)}.png"
                        st.markdown(f"**Aktueller Club:** {c_name}")
                        st.image(logo_url, width=60)
                    else:
                        st.write(f"**Aktueller Club:** {c_name}")
                
                with stat_col2:
                    st.write(f"**Grösse:** {int(p_data['height_in_cm'])} cm" if pd.notna(p_data['height_in_cm']) else "**Grösse:** Unbekannt")
                    st.write(f"**Länderspiele:** {int(p_data['international_caps'])}" if pd.notna(p_data['international_caps']) else "**Länderspiele:** 0")
                    st.write(f"**Länderspieltore:** {int(p_data['international_goals'])}" if pd.notna(p_data['international_goals']) else "**Länderspieltore:** 0")

                st.divider()
                # Key Metrics at a glance
                m1, m2 = st.columns(2)
                m1.metric("Aktueller Marktwert", f"€{p_data['market_value_in_eur']:,.0f}".replace(",", "."))
                m2.metric("Höchster Marktwert", f"€{p_data['highest_market_value_in_eur']:,.0f}".replace(",", "."))

            st.divider()

        # 1. Filter data for the selected player
        p_injuries = filtered_df[filtered_df['player_id'] == selected_pid].copy()
        p_valuations = val_df[val_df['player_id'] == selected_pid].sort_values('date').copy()

        if not p_valuations.empty:
            st.subheader(f"Marktwertverlauf von {p_name}")

            # Filter for specific injuries to show in chart based on the top search
            if not p_injuries.empty:
                if selected_injury_risk != "Alle Verletzungen":
                    visible_injuries = p_injuries[p_injuries['Injury'] == selected_injury_risk]
                else:
                    visible_injuries = p_injuries
            else:
                visible_injuries = pd.DataFrame()

            # Plotly Chart
            fig_mv = go.Figure()

            # Add Market Value Line
            fig_mv.add_trace(go.Scatter(
                x=p_valuations['date'],
                y=p_valuations['market_value_in_eur'],
                mode='lines',
                name='Marktwert (EUR)',
                line=dict(color='#2563EB', width=3),
                customdata=p_valuations[['current_club_name']],
                hovertemplate='<b>Datum:</b> %{x|%d.%m.%Y}<br><b>Marktwert:</b> €%{y:,.0f}<br><b>Club:</b> %{customdata[0]}<extra></extra>'
            ))

            # Add Injury vrects
            if not visible_injuries.empty:
                for _, row in visible_injuries.iterrows():
                    start = row['injury_from_parsed']
                    end = row['injury_until_parsed']
                    if pd.notna(start) and pd.notna(end):
                        # Determine color
                        color = get_injury_color(row['injury_category'], row['Injury'])
                        duration_days = int(row['Days'])
                        
                        fig_mv.add_vrect(
                            x0=start, x1=end,
                            fillcolor=color, opacity=0.3,
                            layer="below", line_width=0,
                            annotation_text=f"<b>{row['Injury']}</b> ({duration_days} Tage)",
                            annotation_position="top left",
                            annotation_font_size=11,
                            annotation_font_color=color if color != "yellow" else "#B8860B", # Better contrast for yellow
                        )

            fig_mv.update_layout(
                xaxis_title="Datum",
                yaxis_title="Marktwert in EUR",
                height=500,
                hovermode='x unified',
                template="plotly_white"
            )

            # Add Club Logos for every data point
            if 'current_club_id' in p_valuations.columns:
                # Dynamic sizing based on the max market value of the visible chart
                max_mv = p_valuations['market_value_in_eur'].max()
                
                for _, v_row in p_valuations.iterrows():
                    c_id = v_row['current_club_id']
                    if pd.notna(c_id):
                        logo_url = f"https://tmssl.akamaized.net/images/wappen/tiny/{int(c_id)}.png"
                        fig_mv.add_layout_image(
                            dict(
                                source=logo_url,
                                xref="x",
                                yref="y",
                                x=v_row['date'],
                                y=v_row['market_value_in_eur'],
                                sizex=30 * 24 * 60 * 60 * 1000, # Balanced to ~30 days
                                sizey=max_mv * 0.12 if max_mv > 0 else 500000, # Balanced based on max value
                                xanchor="center",
                                yanchor="middle",
                                opacity=1.0,
                                layer="above"
                            )
                        )

            st.plotly_chart(fig_mv, use_container_width=True)

            # 2. Injury-Value-Delta (Schwerste Verletzung)
            if not p_injuries.empty:
                st.divider()
                st.subheader("⚠️ Finanzieller Verletzungs-Impact (Delta)")
                
                # Find most severe injury
                major_injury = p_injuries.sort_values('Days', ascending=False).iloc[0]
                start_date = major_injury['injury_from_parsed']
                end_date = major_injury['injury_until_parsed']
                
                # Market value BEFORE injury
                val_before = p_valuations[p_valuations['date'] <= start_date]
                # Market value DURING or AFTER injury
                val_after = p_valuations[p_valuations['date'] >= start_date] # We look from start onwards
                
                if not val_before.empty and not val_after.empty:
                    v_before = val_before.iloc[-1]['market_value_in_eur']
                    
                    # For val_after, we look for the first value recorded after the injury ended or nearing the end
                    val_after_end = p_valuations[p_valuations['date'] >= end_date]
                    if not val_after_end.empty:
                        v_after = val_after_end.iloc[0]['market_value_in_eur']
                    else:
                        v_after = val_after.iloc[-1]['market_value_in_eur']
                    
                    delta_pct = ((v_after - v_before) / v_before) * 100
                    delta_abs = v_after - v_before
                    
                    m1, m2 = st.columns(2)
                    m1.metric("Schwerste Verletzung", major_injury['Injury'])
                    m2.metric("Dauer", f"{major_injury['Days']} Tage")

                    m3, m4, m5 = st.columns(3)
                    m3.metric("Marktwert (Vorher)", f"€{v_before:,.0f}".replace(",", "."))
                    m4.metric("Marktwert (Nachher)", f"€{v_after:,.0f}".replace(",", "."))
                    
                    delta_color = "inverse" if delta_pct < 0 else "normal"
                    m5.metric("Veränderung (Delta)", f"{delta_pct:.1f}%", delta_color="normal")
                    
                    if delta_pct < 0:
                        st.error(f"Der Spieler hat während/nach dieser Verletzung **€{abs(delta_abs):,.0f}** ({abs(delta_pct):.1f}%) seines Marktwertes verloren.".replace(",", "."))
                    else:
                        st.success(f"Trotz der Verletzung konnte der Spieler seinen Marktwert halten oder steigern (+€{delta_abs:,.0f} / +{delta_pct:.1f}%).".replace(",", "."))
                
                # 3. Detailed Per-Injury Delta Analysis Table
                st.divider()
                st.subheader("📊 Detaillierte Analyse pro Verletzung")
                st.markdown("Diese Tabelle zeigt den Marktwert-Impact für jede individuelle Verletzungsphase des Spielers.")
                
                delta_records = []
                for _, row in p_injuries.sort_values('injury_from_parsed', ascending=False).iterrows():
                    i_start = row['injury_from_parsed']
                    i_end = row['injury_until_parsed']
                    
                    # Find closest valuation before
                    val_before_row = p_valuations[p_valuations['date'] <= i_start]
                    if not val_before_row.empty:
                        v_pre = val_before_row.iloc[-1]['market_value_in_eur']
                    else:
                        v_pre = p_valuations.iloc[0]['market_value_in_eur'] # Fallback
                        
                    # Find first valuation after or nearing end
                    val_after_row = p_valuations[p_valuations['date'] >= i_end]
                    if not val_after_row.empty:
                        v_post = val_after_row.iloc[0]['market_value_in_eur']
                    else:
                        v_post = p_valuations.iloc[-1]['market_value_in_eur'] # Fallback
                        
                    diff_abs = v_post - v_pre
                    diff_pct = (diff_abs / v_pre * 100) if v_pre > 0 else 0
                    
                    delta_records.append({
                        "Verletzung": row['Injury'],
                        "Datum": i_start.strftime('%d.%m.%Y'),
                        "Dauer": f"{int(row['Days'])} Tage",
                        "Marktwert Vorher": f"€{v_pre:,.0f}".replace(",", "."),
                        "Marktwert Nachher": f"€{v_post:,.0f}".replace(",", "."),
                        "Delta (%)": f"{diff_pct:+.1f}%"
                    })
                
                if delta_records:
                    delta_analysis_df = pd.DataFrame(delta_records)
                    st.dataframe(
                        delta_analysis_df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Keine ausreichenden Daten für eine detaillierte Delta-Analyse vorhanden.")
                
                st.divider()
                st.subheader("💼 Vertragsrisikoanalyse")
                st.markdown("""
                Diese Analyse bewertet das **Verletzungsrisiko** anhand historischer Ausfallzeiten und 
                quantifiziert die finanzielle Auswirkung auf den Marktwert über eine typische 5-Jahres-Karriereerwartung.
                """)
                
                # Alle Verletzungsdaten des Spielers laden
                player_all_data = df[df['player_id'] == selected_pid]
                player_market_value = p_info['market_value_in_eur'].iloc[0] if not p_info.empty else 0
                
                risk_metrics = calculate_contract_risk(player_all_data, player_market_value)
                
                if risk_metrics:
                    # Metriken-Display
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "💰 Kapitalverlust durch Ausfalltage",
                            f"€{risk_metrics['financial_impact']:,.0f}".replace(",", "."),
                            f"{-risk_metrics['risk_percentage']:.1f}% vom Marktwert"
                        )
                    
                    with col2:
                        st.metric(
                            "⏱️ Ø Ausfalltage pro Verletzung",
                            f"{risk_metrics['avg_days_per_injury']:.1f}",
                            help=f"{risk_metrics['total_injuries']} Verletzungen total"
                        )
                    
                    with col3:
                        st.metric(
                            "📊 Ø Geschätzter jährlicher Wertverlust",
                            f"€{risk_metrics['annual_impact']:,.0f}".replace(",", "."),
                            help="über eine 5-Jahres-Karriere hochgerechnet"
                        )
                    
                    # Risiko-Level & Empfehlung
                    col_risk1, col_risk2 = st.columns([1.5, 2.5])
                    
                    with col_risk1:
                        # Farbige Box für Risiko-Level
                        if risk_metrics['risk_color'] == 'red':
                            st.error(f"**{risk_metrics['risk_level']}**")
                        elif risk_metrics['risk_color'] == 'orange':
                            st.warning(f"**{risk_metrics['risk_level']}**")
                        else:
                            st.success(f"**{risk_metrics['risk_level']}**")
                    
                    with col_risk2:
                        st.info(risk_metrics['contract_action'])
                else:
                    st.warning("Marktwertdaten nicht verfügbar für Risikoanalyse.")
        else:
            st.warning(f"Keine Marktwert-Historie für '{p_name}' gefunden. Eventuell weicht der Name in der Transfermarkt-Datenbank leicht ab.")
    elif selected_injury_risk != "Alle Verletzungen":
        st.subheader(f"🩹 Katalog: {selected_injury_risk}")
        
        # Filter players with this injury and merge with full player info for images
        injury_players = df[df['Injury'] == selected_injury_risk].copy()
        
        if not injury_players.copy().empty:
            # Join with players_info_df to get image_url
            injury_players = pd.merge(
                injury_players, 
                players_info_df[['player_id', 'image_url']], 
                on='player_id', 
                how='left'
            )
            
            # Sort Option
            sort_by = st.radio("Katalog sortieren nach:", ["Höchster Marktwert", "Meiste Ausfalltage"], horizontal=True)
            
            # Group by player_id and player_name to get metadata and keep duplicates separate
            catalog_df = injury_players.groupby(['player_id', 'player_name']).agg({
                'market_value_in_eur': 'first',
                'club': 'first',
                'league': 'first',
                'Days': 'max', # Use max for sorting to see the worst instance
                'image_url': 'first'
            }).reset_index()
            
            if "Marktwert" in sort_by:
                catalog_df = catalog_df.sort_values('market_value_in_eur', ascending=False)
            else:
                catalog_df = catalog_df.sort_values('Days', ascending=False)
            
            # --- Advanced Insight: Market Impact Trend ---
            # We take a sample of the top 20 players to estimate the impact trend
            sample_players = catalog_df.head(20)[['player_id', 'player_name']].values.tolist()
            sample_deltas = []
            
            # This is a bit simplified to avoid heavy computation
            for pid, sp in sample_players:
                p_inj = df[(df['player_id'] == pid) & (df['Injury'] == selected_injury_risk)].sort_values('Days', ascending=False)
                if not p_inj.empty:
                    row = p_inj.iloc[0]
                    p_vals = val_df[val_df['player_id'] == pid].sort_values('date')
                    if not p_vals.empty:
                        # Value before
                        v_pre_df = p_vals[p_vals['date'] <= row['injury_from_parsed']]
                        v_post_df = p_vals[p_vals['date'] >= row['injury_until_parsed']]
                        if not v_pre_df.empty and not v_post_df.empty:
                            v_pre = v_pre_df.iloc[-1]['market_value_in_eur']
                            v_post = v_post_df.iloc[0]['market_value_in_eur']
                            if v_pre > 0:
                                sample_deltas.append((v_post - v_pre) / v_pre)

            avg_impact = (sum(sample_deltas) / len(sample_deltas) * 100) if sample_deltas else None
            
            avg_days = catalog_df['Days'].mean()
            total_players = len(catalog_df)
            
            # Display metrics
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Betroffene Spieler", total_players)
            m_col2.metric("Ø Ausfalldauer", f"{avg_days:.1f} Tage")
            if avg_impact is not None:
                m_col3.metric("Ø Marktwert-Trend", f"{avg_impact:+.1f}%", delta=f"{avg_impact:.1f}%", delta_color="normal")
            else:
                m_col3.metric("Ø Marktwert-Trend", "N/A")

            if avg_impact is not None:
                if avg_impact < -5:
                    st.error(f"⚠️ **Finanzielles Risiko:** Diese Verletzung korreliert bei den Top-Spielern mit einem deutlichen Marktwertverlust von durchschnittlich **{abs(avg_impact):.1f}%**.")
                elif avg_impact > 5:
                    st.success(f"📈 **Resilienz:** Erstaunlicherweise zeigt die Datenlage bei dieser Verletzung einen positiven Marktwert-Trend (+{avg_impact:.1f}%). Dies deutet darauf hin, dass Spieler oft stärker zurückkommen oder die Verletzung in eine Phase des Marktwert-Wachstums fällt.")
                else:
                    st.info(f"⚖️ **Neutraler Impact:** Der Marktwert bleibt nach dieser Verletzung im Durchschnitt stabil ({avg_impact:+.1f}%).")

            st.divider()
            
            # Display grid
            display_limit = st.session_state['risk_display_count']
            display_df = catalog_df.head(display_limit)
            
            for i in range(0, len(display_df), 2):
                cols = st.columns(2)
                for j in range(2):
                    if i + j < len(display_df):
                        player = display_df.iloc[i + j]
                        p_name = player['player_name']
                        p_id = player['player_id']
                        
                        # --- Calculate Individual Impact for this player and injury ---
                        # Find the longest instance of this injury for this player
                        p_inj = df[(df['player_id'] == p_id) & (df['Injury'] == selected_injury_risk)].sort_values('Days', ascending=False)
                        
                        impact_data = None
                        if not p_inj.empty:
                            row = p_inj.iloc[0]
                            p_vals = val_df[val_df['player_id'] == p_id].sort_values('date')
                            if not p_vals.empty:
                                val_before_df = p_vals[p_vals['date'] <= row['injury_from_parsed']]
                                val_after_df = p_vals[p_vals['date'] >= row['injury_until_parsed']]
                                
                                if not val_before_df.empty and not val_after_df.empty:
                                    v_pre = val_before_df.iloc[-1]['market_value_in_eur']
                                    v_post = val_after_df.iloc[0]['market_value_in_eur']
                                    diff_pct = ((v_post - v_pre) / v_pre * 100) if v_pre > 0 else 0
                                    impact_data = {
                                        'pre': v_pre,
                                        'post': v_post,
                                        'pct': diff_pct,
                                        'days': row['Days'],
                                        'date': row['injury_from_parsed'].strftime('%d.%m.%y'),
                                        'end_date': row['injury_until_parsed'].strftime('%d.%m.%y') if pd.notna(row['injury_until_parsed']) else "?"
                                    }

                        with cols[j]:
                            with st.container(border=True):
                                c1, c2 = st.columns([1, 2])
                                with c1:
                                    if pd.notna(player['image_url']):
                                        st.image(player['image_url'], use_container_width=True)
                                    else:
                                        st.write("👤")
                                with c2:
                                    st.markdown(f"**{p_name}**")
                                    st.write(f"{player['club']} ({player['league']})")
                                    
                                    if impact_data:
                                        # Display Impact
                                        color = "red" if impact_data['pct'] < -2 else "green" if impact_data['pct'] > 2 else "gray"
                                        st.markdown(f"""
                                        <div style="font-size: 0.85rem; background: #F8FAFC; padding: 8px; border-radius: 5px; border-left: 4px solid {color}; color: #0F172A;">
                                            <b style="color: #0F172A;">Impact:</b> <span style="color: {color}; font-weight: bold;">{impact_data['pct']:+.1f}%</span><br>
                                            <span style="color: #475569;">€{impact_data['pre']/1e6:.1f}M &rarr; €{impact_data['post']/1e6:.1f}M</span><br>
                                            <span style="font-size: 0.75rem; color: #64748B;">📅 {impact_data['date']} - {impact_data['end_date']} <b>({int(impact_data['days'])} Tage)</b></span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        st.write(f"Marktwert: €{player['market_value_in_eur']:,.0f}".replace(",", "."))
                                    
                                    st.write("") # Spacer
                                    p_label = next((k for k, v in player_options_map.items() if v == p_id), p_name)
                                    if st.button(f"Profil: {p_label}", key=f"risk_btn_{p_id}"):
                                        st.session_state['risk_selected_player'] = p_label
                                        st.rerun()
            
            if len(catalog_df) > display_limit:
                if st.button("Weitere 50 Spieler laden"):
                    st.session_state['risk_display_count'] += 50
                    st.rerun()
        else:
            st.info("Keine Daten für diese Verletzung gefunden.")
            
    else:
        st.info("💡 Wähle eine Verletzung aus, um den Marktwert-Katalog zu sehen, oder suche direkt nach einem Spieler.")

