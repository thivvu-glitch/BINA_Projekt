import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import os

# Page Config
st.set_page_config(page_title="Europäische Fussballverletzungen Dashboard", layout="wide")

# Title and Description
st.title("⚽ Europäische Fussballverletzungen (2020-2025)")
st.markdown("""
Dieses Dashboard ermöglicht die Analyse von Verletzungsmustern im europäischen Profifussball.
Basiert auf der **CPA Management Accounting Guideline** für datengesteuerte Entscheidungen.
""")

# Load Data
@st.cache_data
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "Data/cleaned_dataset_final.csv")
    df = pd.read_csv(path, encoding='utf8', delimiter=',')
    
    # Cleaning 'Games missed'
    df['Games missed'] = pd.to_numeric(df['Games missed'], errors='coerce').fillna(0).astype(int)
    # Dates
    df['injury_from_parsed'] = pd.to_datetime(df['injury_from_parsed'], errors='coerce')
    df['Month'] = df['injury_from_parsed'].dt.month_name(locale="de_DE.UTF-8")  # 'locale="de_DE.utf8"' does not work on macOS, 'locale="de_DE.UTF-8"' does work on Windows and macOS
    df['Month_Num'] = df['injury_from_parsed'].dt.month
    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("Filteroptionen")

# League Filter
leagues = sorted(df['league'].unique().tolist())
selected_leagues = st.sidebar.multiselect("Ligen auswählen", leagues, default=leagues)

# Season Filter
seasons = sorted(df['Season'].unique().tolist())
selected_seasons = st.sidebar.multiselect("Saisons auswählen", seasons, default=seasons)

# Player Search
player_search = st.sidebar.text_input("Spieler suchen (z. B. Sasa Kalajdzic)")

st.sidebar.markdown("---")
st.sidebar.caption("Navigation erfolgt über Tabs im Hauptbereich.")

# Filter Data
filtered_df = df[
    (df['league'].isin(selected_leagues)) &
    (df['Season'].isin(selected_seasons))
]

if player_search:
    filtered_df = filtered_df[filtered_df['player_name'].str.contains(player_search, case=False, na=False)]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Gesamtverletzungen", f"{len(filtered_df):,}".replace(",", "."))
col2.metric("Ausfalltage insgesamt", f"{filtered_df['Days'].sum():,}".replace(",", "."))
col3.metric("Ø Tage pro Verletzung", f"{filtered_df['Days'].mean():.1f}".replace(".", ",") if len(filtered_df) > 0 else "0")
col4.metric("Ø Verpasste Spiele", f"{filtered_df['Games missed'].mean():.1f}".replace(".", ",") if len(filtered_df) > 0 else "0")

if filtered_df.empty:
    st.warning("Keine Daten für die gewählten Filter. Bitte passe Liga, Saison oder Spieler an.")

tab_overview, tab_trends, tab_tables, tab_dddm = st.tabs([
    "Übersicht",
    "Zeit & Liga",
    "Tabellen",
    "DDDM Entscheidungen"
])

with tab_overview:
    st.subheader("Kernvergleich der Ligen")
    c1, c2 = st.columns(2)

    with c1:
        league_counts = filtered_df['league'].value_counts().reset_index()
        league_counts.columns = ['Liga', 'Verletzungen']
        fig_league = px.bar(
            league_counts,
            x='Verletzungen',
            y='Liga',
            orientation='h',
            color='Verletzungen',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_league, use_container_width=True)

    with c2:
        severity = filtered_df.groupby('league')['Days'].mean().sort_values(ascending=False).reset_index()
        fig_sev = px.bar(
            severity,
            x='Days',
            y='league',
            orientation='h',
            labels={'Days': 'Ø Ausfalltage', 'league': 'Liga'},
            color='Days',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_sev, use_container_width=True)

    st.subheader("Top 'Pechvögel' (Längste Ausfallzeiten)")
    top_p = filtered_df.groupby('player_name')['Days'].sum().sort_values(ascending=False).head(15).reset_index()
    fig_top = px.bar(
        top_p,
        x='Days',
        y='player_name',
        orientation='h',
        color='Days',
        color_continuous_scale='Viridis',
        labels={'Days': 'Ausfalltage', 'player_name': 'Spieler'}
    )
    st.plotly_chart(fig_top, use_container_width=True)

with tab_trends:
    st.subheader("Saisonale Muster im Ligenvergleich")
    monthly = filtered_df.groupby(['Month_Num', 'Month', 'league']).size().reset_index(name='Anzahl').sort_values('Month_Num')
    fig_month = px.line(
        monthly,
        x='Month',
        y='Anzahl',
        color='league',
        markers=True,
        title="Verletzungen im Jahresverlauf nach Ligen",
        labels={'Month': 'Monat', 'Anzahl': 'Anzahl Verletzungen', 'league': 'Liga'}
    )
    st.plotly_chart(fig_month, use_container_width=True)

    st.subheader("Verletzungsentwicklung über die Saisons")
    season_counts = filtered_df.groupby(['Season', 'league']).size().reset_index(name='Anzahl')
    if not season_counts.empty:
        fig_season = px.bar(
            season_counts,
            x='Season',
            y='Anzahl',
            color='league',
            barmode='group',
            labels={'Season': 'Saison', 'Anzahl': 'Anzahl Verletzungen', 'league': 'Liga'}
        )
        st.plotly_chart(fig_season, use_container_width=True)
    else:
        st.info("Keine Daten für diesen Vergleich verfügbar.")

    st.subheader("Automatisches Fazit zum Ligenvergleich")
    if len(selected_leagues) >= 2 and not filtered_df.empty:
        most_injuries_league = filtered_df['league'].value_counts().idxmax()
        most_severe_league = filtered_df.groupby('league')['Days'].mean().idxmax()

        monthly_peak = filtered_df.groupby(['league', 'Month'])['Days'].count().reset_index()
        monthly_peak.columns = ['league', 'Month', 'Count']
        monthly_peak = monthly_peak.loc[monthly_peak.groupby('league')['Count'].idxmax()]

        fazit_text = f"**Vergleich der ausgewählten Ligen ({', '.join(selected_leagues)}):**\n\n"
        fazit_text += f"- **Häufigkeit:** Die absolute Mehrheit der Verletzungen weist die **{most_injuries_league}** auf.\n"
        fazit_text += f"- **Schweregrad:** Die längsten durchschnittlichen Ausfallzeiten gibt es in der **{most_severe_league}**.\n"
        fazit_text += "- **Saisonale Spitzen (Wann steigen die Verletzungen?):**\n"

        for _, row in monthly_peak.iterrows():
            fazit_text += f"  - In der **{row['league']}** gibt es den höchsten Anstieg an Verletzungen im **{row['Month']}**.\n"

        st.info(fazit_text)
    elif len(selected_leagues) < 2:
        st.info("Wähle in der Seitenleiste mindestens zwei Ligen aus, um ein automatisches Vergleichs-Fazit zu generieren.")
    else:
        st.info("Keine Daten für ein Fazit vorhanden.")

with tab_tables:
    st.subheader("Detaillierte Tabellenansicht")
    comparison_mode = st.radio(
        "Tabellen gruppieren nach:",
        options=["Liga", "Saison"],
        horizontal=True
    )

    if comparison_mode == "Liga":
        if not selected_leagues:
            st.info("Bitte wähle mindestens eine Liga aus, um die Tabellen zu sehen.")
        else:
            for league in selected_leagues:
                league_df = filtered_df[filtered_df['league'] == league]
                with st.expander(f"{league} ({len(league_df)} Einträge)", expanded=False):
                    if league_df.empty:
                        st.write("Keine Daten für die aktuellen Filter in dieser Liga.")
                    else:
                        display_df = league_df[['Season', 'player_name', 'club', 'Injury', 'Days', 'Games missed']].copy()
                        display_df.columns = ['Saison', 'Spieler', 'Verein', 'Verletzung', 'Ausfalltage', 'Verpasste Spiele']
                        display_df = display_df.sort_values('Ausfalltage', ascending=False)
                        st.dataframe(display_df, use_container_width=True, hide_index=True)

    elif comparison_mode == "Saison":
        if not selected_seasons:
            st.info("Bitte wähle mindestens eine Saison aus, um die Tabellen zu sehen.")
        else:
            for season in selected_seasons:
                season_df = filtered_df[filtered_df['Season'] == season]
                with st.expander(f"Saison {season} ({len(season_df)} Einträge)", expanded=False):
                    if season_df.empty:
                        st.write("Keine Daten für die aktuellen Filter in dieser Saison.")
                    else:
                        display_df = season_df[['league', 'player_name', 'club', 'Injury', 'Days', 'Games missed']].copy()
                        display_df.columns = ['Liga', 'Spieler', 'Verein', 'Verletzung', 'Ausfalltage', 'Verpasste Spiele']
                        display_df = display_df.sort_values('Ausfalltage', ascending=False)
                        st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab_dddm:
    st.subheader("📊 DDDM: Risikoanalyse für Kadermanagement (CPA)")
    st.markdown("""
    **Anwendungsfall:** Soll der Vertrag eines Spielers verlängert werden?
    Diese prädiktive Metrik berechnet einen Risiko-Score basierend auf historischen Ausfalltagen, um finanzielle Fehlinvestitionen zu vermeiden.
    """)

    if player_search and not filtered_df.empty:
        player_data = filtered_df[filtered_df['player_name'].str.contains(player_search, case=False, na=False)]

        if not player_data.empty:
            total_days_missed = player_data['Days'].sum()
            total_injuries = len(player_data)

            if total_days_missed > 150:
                risk_level = "Hohes Risiko 🔴"
                action_recommendation = "Empfehlung: Vertragsverlängerung kritisch prüfen. Ggf. leistungsbezogene Verträge anbieten (Pay-per-Play)."
            elif total_days_missed > 50:
                risk_level = "Mittleres Risiko 🟡"
                action_recommendation = "Empfehlung: Standardvertrag, aber enge Abstimmung mit dem medizinischen Personal für Belastungssteuerung."
            else:
                risk_level = "Geringes Risiko 🟢"
                action_recommendation = "Empfehlung: Unbedenkliche Verlängerung aus medizinischer Sicht. Stabiler Asset-Value."

            colA, colB = st.columns(2)
            with colA:
                st.metric("Spieler", player_data['player_name'].iloc[0])
                st.metric("Verletzungshistorie (Anzahl)", total_injuries)
                st.metric("Gesamte Ausfalltage", total_days_missed)

            with colB:
                st.info(f"**Kalkuliertes Investment-Risiko:** {risk_level}")
                st.warning(action_recommendation)

            st.dataframe(player_data[['Season', 'Injury', 'Days', 'Games missed']], use_container_width=True, hide_index=True)
    else:
        st.info("Gib links einen Spielernamen ein, um die Risikoanalyse zu aktivieren.")

    st.divider()
    st.subheader("💡 DDDM: Präskriptive Ressourcenallokation (Medical Budget)")
    st.markdown("""
    **Anwendungsfall:** Wo soll das Budget für medizinische Ausrüstung und Personal im nächsten Quartal investiert werden?
    Dieser Bereich aggregiert die Ausfalltage nach Verletzungsart, um die teuersten Schwachstellen im Kader zu identifizieren und Investitionsentscheidungen (Capital Project Appraisal) zu lenken.
    """)

    if not filtered_df.empty:
        injury_cost = filtered_df.groupby('Injury').agg(
            Total_Days=('Days', 'sum'),
            Count=('Injury', 'count')
        ).reset_index().sort_values(by='Total_Days', ascending=False)

        top_injury = injury_cost.iloc[0]
        c_med1, c_med2 = st.columns([2, 1])

        with c_med1:
            fig_treemap = px.treemap(
                injury_cost.head(15),
                path=['Injury'],
                values='Total_Days',
                title="Die 15 teuersten Verletzungsarten (gemessen in Ausfalltagen)",
                color='Total_Days',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_treemap, use_container_width=True)

        with c_med2:
            st.error(f"**Haupttreiber für Ausfalltage:** {top_injury['Injury'].title()}")
            st.write(f"Verursachte in der Auswahl **{top_injury['Total_Days']} Tage** Ausfall bei {top_injury['Count']} Einzelfällen.")
            st.markdown("**CPA / Investitionsempfehlung:**")
            st.success(f"""
            Basierend auf den Daten sollte der höchste ROI (Return on Investment) durch gezielte Prävention von **{top_injury['Injury'].title()}** erreicht werden.

            **Handlungsvorschläge:**
            1. Allokation von Budget für Spezialgeräte zur Prävention/Reha dieser Verletzungsart.
            2. Schulung oder Einstellung eines Spezialisten für dieses Gebiet.
            """)
    else:
        st.info("Keine Daten für die Budgetanalyse verfügbar.")

st.markdown("---")
st.caption("Entwickelt für Senior Data Scientist Analyse (CPA Framework).")