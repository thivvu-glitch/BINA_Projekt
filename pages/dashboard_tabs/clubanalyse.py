import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def render(df, filtered_df, selected_seasons, DEFAULT_SEASON, club_options, season_options):
    def season_start_year(season: str) -> int:
        try:
            return int(str(season).split("/")[0])
        except (ValueError, IndexError):
            return 9999

    def checkSeason(seasons_to_check=None):
        seasons_to_check = seasons_to_check if seasons_to_check is not None else selected_seasons
        if any(season_start_year(season) < season_start_year(DEFAULT_SEASON[0]) for season in seasons_to_check):
            return st.warning(
                "Du hast ältere Saisons als 24/25 ausgewählt. Die Kaderzusammensetzung kann dadurch vom aktuellen Kader abweichen, "
                "weil Transfers, Abgänge und Neuzugänge nicht mehr exakt dem heutigen Team entsprechen."
            , icon="⚠️")

    st.header("💼 Clubanalyse")    
    st.markdown("""
    **Welche Fragen werden dir in diesem Register beantwortet?**                
    - Welche Verletzungsarten verursachen die meisten Ausfalltage?
    - Bei welchen Verletzungen besteht der höchste wirtschaftliche Schaden für den Club?
    - Wo sollte das medizinische Budget investiert werden, um den grössten ROI zu erzielen?       
    - Welche Präventions- oder Reha-Massnahmen haben die höchste Priorität?       
                
    **Für wen?**
    - Club-Manager
    - CEO / CFO
    - Sportdirektor
    - Medizinisches Personal
    
    **Was sieht man?**
    - **Verletzungsübersicht:** Häufigste Verletzungen mit den höchsten Ausfalltage anhand der gesetzten Filter
    - **Ressourcenplanung:** Budget-Allokation für Medizin und Prävention
    - **Capital Project Appraisal (CPA):** ROI von medizinischen Investitionen
    """)
    st.divider()
    

    st.subheader("🏥 Präskriptive Ressourcenallokation (Medical Budget)")
    st.markdown("""
    **Anwendungsfall:** Wo soll das Budget für medizinische Ausrüstung und Personal im nächsten Quartal investiert werden?
    Dieser Bereich aggregiert die Ausfalltage nach Verletzungsart, um die teuersten Schwachstellen im Kader zu identifizieren und Investitionsentscheidungen (Capital Project Appraisal) zu lenken.
    """)

    st.markdown("### 🔎 Filter für Ressourcenallokation")
    dddm_filter_col1, dddm_filter_col2, dddm_filter_col3 = st.columns(3)

    with dddm_filter_col1:
        st.selectbox(
            "Club auswählen",
            options=club_options,
            key='dddm_filter_club',
            help="Begrenzt die Analyse auf einen bestimmten Club."
        )

    with dddm_filter_col2:
        if 'dddm_filter_seasons' not in st.session_state or not st.session_state['dddm_filter_seasons']:
            st.session_state['dddm_filter_seasons'] = season_options
            
        st.multiselect(
            "Saisons auswählen",
            options=season_options,
            default=season_options,  # Standardmäßig alle Saisons ausgewählt
            key='dddm_filter_seasons',
            help="Analysiert nur die gewählten Saisons."
        )

    dddm_league_source_df = df.copy()
    if st.session_state['dddm_filter_club'] != "Alle Clubs":
        dddm_league_source_df = dddm_league_source_df[dddm_league_source_df['club'] == st.session_state['dddm_filter_club']]
    dddm_league_options = sorted(dddm_league_source_df['league'].dropna().unique().tolist())
    st.session_state['dddm_filter_leagues'] = [l for l in st.session_state['dddm_filter_leagues'] if l in dddm_league_options]
    if not st.session_state['dddm_filter_leagues']:
        st.session_state['dddm_filter_leagues'] = dddm_league_options

    with dddm_filter_col3:
        st.multiselect(
            "Liga auswählen",
            options=dddm_league_options,
            key='dddm_filter_leagues',
            help="Analysiert nur die gewählten Ligen."
        )

    dddm_filtered_df = df.copy()
    if st.session_state['dddm_filter_club'] != "Alle Clubs":
        dddm_filtered_df = dddm_filtered_df[dddm_filtered_df['club'] == st.session_state['dddm_filter_club']]
    if st.session_state['dddm_filter_seasons']:
        dddm_filtered_df = dddm_filtered_df[dddm_filtered_df['Season'].isin(st.session_state['dddm_filter_seasons'])]
    if st.session_state['dddm_filter_leagues']:
        dddm_filtered_df = dddm_filtered_df[dddm_filtered_df['league'].isin(st.session_state['dddm_filter_leagues'])]

    st.caption(
        f"Aktive DDDM-Filter: Club = {st.session_state['dddm_filter_club']}, "
        f"Saisons = {', '.join(st.session_state['dddm_filter_seasons']) if st.session_state['dddm_filter_seasons'] else 'Keine'}, "
        f"Ligen = {', '.join(st.session_state['dddm_filter_leagues']) if st.session_state['dddm_filter_leagues'] else 'Keine'}"
    )

    if not dddm_filtered_df.empty:
        checkSeason(st.session_state['dddm_filter_seasons'])
        injury_cost = dddm_filtered_df.groupby('Injury').agg(
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
            fig_treemap.update_traces(
                texttemplate="%{label}<br>%{value} Ausfalltage",
                textinfo='text'
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




