import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

import os

# Page Config
st.set_page_config(page_title="Europäische Fussballverletzungen Dashboard", layout="wide")

# Title and Description
st.title("⚽ Europäische Fussballverletzungen (2020-2025)")

# Load Data
@st.cache_data
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "../Data/cleaned_dataset_final.csv")
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

# Defaults
DEFAULT_SEASON = "24/25"

# Club Filter (global)
clubs = sorted(df['club'].dropna().unique().tolist())
club_options = ["Alle Clubs"] + clubs

if 'filter_club' not in st.session_state:
    st.session_state['filter_club'] = "Alle Clubs"
if 'filter_leagues' not in st.session_state:
    st.session_state['filter_leagues'] = sorted(df['league'].dropna().unique().tolist())
if 'filter_seasons' not in st.session_state:
    st.session_state['filter_seasons'] = [DEFAULT_SEASON] if DEFAULT_SEASON in df['Season'].dropna().unique().tolist() else sorted(df['Season'].dropna().unique().tolist())
if 'filter_players' not in st.session_state:
    st.session_state['filter_players'] = []

# Reset button
if st.sidebar.button("Filter auf Default zurücksetzen"):
    st.session_state['filter_club'] = "Alle Clubs"
    st.session_state['filter_leagues'] = sorted(df['league'].dropna().unique().tolist())
    st.session_state['filter_seasons'] = [DEFAULT_SEASON] if DEFAULT_SEASON in df['Season'].dropna().unique().tolist() else sorted(df['Season'].dropna().unique().tolist())
    st.session_state['filter_players'] = []
    st.rerun()

selected_club_global = st.sidebar.selectbox(
    "Club auswählen",
    club_options,
    key='filter_club',
    help="Dieser globale Filter gilt für alle Dashboards."
)

# League Filter (depends on selected club)
if selected_club_global == "Alle Clubs":
    league_options = sorted(df['league'].dropna().unique().tolist())
else:
    league_options = sorted(df.loc[df['club'] == selected_club_global, 'league'].dropna().unique().tolist())

st.session_state['filter_leagues'] = [l for l in st.session_state['filter_leagues'] if l in league_options]
if not st.session_state['filter_leagues']:
    st.session_state['filter_leagues'] = league_options

selected_leagues = st.sidebar.multiselect("Ligen auswählen", league_options, key='filter_leagues')

# Season Filter
season_options = sorted(df['Season'].dropna().unique().tolist())
st.session_state['filter_seasons'] = [s for s in st.session_state['filter_seasons'] if s in season_options]
if not st.session_state['filter_seasons']:
    st.session_state['filter_seasons'] = [DEFAULT_SEASON] if DEFAULT_SEASON in season_options else season_options

selected_seasons = st.sidebar.multiselect("Saisons auswählen", season_options, key='filter_seasons')

# Player Search (limited to selected club and other active filters)
player_source_df = df.copy()
if selected_club_global != "Alle Clubs":
    player_source_df = player_source_df[player_source_df['club'] == selected_club_global]
if selected_leagues:
    player_source_df = player_source_df[player_source_df['league'].isin(selected_leagues)]
if selected_seasons:
    player_source_df = player_source_df[player_source_df['Season'].isin(selected_seasons)]

player_options = sorted(player_source_df['player_name'].dropna().unique().tolist())
st.session_state['filter_players'] = [p for p in st.session_state['filter_players'] if p in player_options]

player_searchBox = st.sidebar.multiselect(
    "Spieler suchen",
    options=player_options,
    key='filter_players',
    max_selections=1,
    help="Suche ist auf den ausgewählten Club (und aktive Liga/Saison-Filter) begrenzt."
)
player_search = player_searchBox[0] if player_searchBox else ""

st.sidebar.markdown("---")
st.sidebar.caption("Navigation erfolgt über Tabs im Hauptbereich.")

# Filter Data
filtered_df = df[
    (df['league'].isin(selected_leagues)) &
    (df['Season'].isin(selected_seasons))
]

if selected_club_global != "Alle Clubs":
    filtered_df = filtered_df[filtered_df['club'] == selected_club_global]

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

tab_overview, tab_injuries, tab_trends, tab_tables, tap_maps, tab_bodymap, tab_dddm = st.tabs([
    "Übersicht",
    "Verletzungsvergleich",
    "Zeit & Liga",
    "Tabellen",
    "Karten",    
    "Bodymap",
    "DDDM Entscheidungen"
])

with tab_overview:
    st.markdown("""
    ### 📊 Für wen ist dieser Dashboard?
    **Zielgruppe:** Analytiker, Trainer, Sport-Manager, Klub-Führung
    
    **Was sieht man?**
    - Vergleich der Verletzungshäufigkeit zwischen Ligen
    - Durchschnittliche Schweregrad (Ausfalltage) nach Liga
    - Die 15 "Pechvögel" mit den längsten kumulierten Ausfallzeiten
    - Schnelle Identifikation von Risiko-Clubs und Risiko-Positionen
    """)
    st.divider()
    
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

with tab_injuries:
    st.markdown("""
    ### 🏥 Für wen ist dieser Dashboard?
    **Zielgruppe:** Medizinisches Personal, Verletzungs-Spezialisten, Trainer, Ligen-Verbände
    
    **Was sieht man?**
    - Detaillierte Analyse einer spezifischen Verletzungsart
    - Verletzungshäufigkeit und Schweregrad nach Liga
    - Zeitliche Verteilung und Muster der Verletzungen
    - Betroffene Spieler und ihre Ausfallzeiten
    - Identifikation von Hochrisiko-Verletzungstypen für Prävention
    """)
    st.divider()
    
    st.subheader("Verletzungsvergleich zwischen den Ligen")
    st.markdown("Analysiere eine spezifische Verletzungsart über alle Ligen hinweg.")

    # Injury Selection
    all_injuries = sorted(df['Injury'].dropna().unique().tolist())
    selected_injury = st.selectbox("Verletzung auswählen", all_injuries, help="Wähle eine Verletzung aus, um den Vergleich zu starten.")

    if selected_injury:
        inj_df = df[df['Injury'] == selected_injury].copy()
        
        # KPIs for this injury
        i_col1, i_col2, i_col3 = st.columns(3)
        i_col1.metric("Fälle Insgesamt", f"{len(inj_df)}")
        i_col2.metric("Ausfalltage Insgesamt", f"{int(inj_df['Days'].sum()):,}".replace(",", "."))
        i_col3.metric("Verpasste Spiele (Summe)", f"{int(inj_df['Games missed'].sum()):,}".replace(",", "."))

        # League comparison charts
        st.divider()
        lc1, lc2 = st.columns(2)

        with lc1:
            st.write(f"**Häufigkeit von '{selected_injury}' nach Liga**")
            inj_league_counts = inj_df['league'].value_counts().reset_index()
            inj_league_counts.columns = ['Liga', 'Anzahl']
            
            fig_inj_l = px.bar(
                inj_league_counts,
                x='Anzahl',
                y='Liga',
                orientation='h',
                color='Anzahl',
                color_continuous_scale='Oranges'
            )
            st.plotly_chart(fig_inj_l, use_container_width=True)

        with lc2:
            st.write(f"**Schweregrad (Ø Tage/Spiele) nach Liga**")
            inj_severity = inj_df.groupby('league')[['Days', 'Games missed']].mean().reset_index()
            
            fig_inj_s = go.Figure()
            fig_inj_s.add_trace(go.Bar(
                y=inj_severity['league'],
                x=inj_severity['Days'],
                name='Ø Ausfalltage',
                orientation='h',
                marker_color='royalblue'
            ))
            fig_inj_s.add_trace(go.Bar(
                y=inj_severity['league'],
                x=inj_severity['Games missed'],
                name='Ø Verpasste Spiele',
                orientation='h',
                marker_color='lightskyblue'
            ))
            fig_inj_s.update_layout(barmode='group', height=400, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_inj_s, use_container_width=True)

        st.divider()
        st.subheader("Grafische Verteilung der Fälle")
        st.write("Jeder Punkt repräsentiert eine Verletzung eines Spielers. Die Farbe zeigt die Liga an.")
        
        if not inj_df.empty:
            fig_scatter = px.scatter(
                inj_df,
                x='injury_from_parsed',
                y='Days',
                color='league',
                size='Games missed',
                hover_data=['player_name', 'club', 'Season'],
                labels={'injury_from_parsed': 'Datum', 'Days': 'Ausfalltage', 'league': 'Liga'},
                title=f"Zeitplan der '{selected_injury}' Fälle"
            )
            fig_scatter.update_layout(xaxis_title="Datum der Verletzung", yaxis_title="Ausfalltage")
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            st.info(f"Die **{inj_league_counts.iloc[0]['Liga']}** dominiert bei dieser Verletzungsart mit {inj_league_counts.iloc[0]['Anzahl']} Fällen.")
        
        with st.expander("Detaillierte Liste der Spieler"):
            st.dataframe(
                inj_df[['player_name', 'club', 'league', 'Season', 'Days', 'Games missed']].sort_values(by='Days', ascending=False), # type: ignore
                use_container_width=True,
                hide_index=True
            )

with tab_trends:
    st.markdown("""
    ### 📈 Für wen ist dieser Dashboard?
    **Zielgruppe:** Strategische Planer, Team-Manager, Athletik-Trainer, Forscher
    
    **Was sieht man?**
    - Saisonale und monatliche Verletzungsmuster
    - Vergleich von Verletzungstrends zwischen verschiedenen Ligen
    - Jahresüber-Vergleiche und historische Entwicklungen
    - Identifikation von Peak-Monaten für Verletzungen
    - Planung von Präventions- und Trainingsprogrammen basierend auf Saisonalität
    """)
    st.divider()
    
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
    st.markdown("""
    ### 📋 Für wen ist dieser Dashboard?
    **Zielgruppe:** Datenanalytiker, Forscher, Klub-Administrator, Medizinische Teams
    
    **Was sieht man?**
    - Vollständige, sortierbare Verletzungsdatenbank
    - Details pro Spieler, Verein und Saison
    - Ausgefallene Spiele und Ausfallzeiten im Detail
    - Export-freundliche Tabellenformate für weitere Analysen
    - Drilldown-Möglichkeit für detaillierte Fallstudien
    """)
    st.divider()
    
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

with tap_maps:
    st.markdown("""
    ### ⚽ Für wen ist dieser Dashboard?
    **Zielgruppe:** Trainer, Athletik-Trainer, Positionscoaches, Scouts
    
    **Was sieht man?**
    - Interaktive Feldpositionen-Visualisierung (virtueller Fußballplatz)
    - Verletzungshäufigkeit nach Spielerposition
    - Positions-spezifische Verletzungsmuster
    - Betroffene Spieler pro Position
    - Strategische Insights für Aufstellung und Spielerrotation
    """)
    st.divider()
    
    st.subheader("Interaktive Karten")
    st.markdown("Analysiere die Verletzungen der Spieler nach Position in den einzelnen Clubs.")

    club_df = filtered_df.copy()
    if not club_df.empty:

        position_coords = {
            "Goalkeeper": (5, 40),

            "Left-Back": (20, 65),
            "Centre-Back": (20, 40),
            "Right-Back": (20, 15),

            "Defensive Midfield": (40, 40),
            "Central Midfield": (55, 40),
            "Attacking Midfield": (70, 40),
            "Midfielder": (55, 52),

            "Left Midfield": (52, 65),
            "Right Midfield": (52, 15),

            "Left Winger": (85, 68),
            "Right Winger": (85, 12),

            "Second Striker": (92, 40),
            "Forward": (105, 40)
        }

        club_df = club_df[club_df['player_position'].isin(position_coords.keys())].copy()

        injury_counts = (
            club_df.groupby("player_position")
            .size()
            .reset_index(name="injury_count")
        )

        injury_counts['x'] = injury_counts['player_position'].map(lambda p: position_coords.get(str(p), (None, None))[0])
        injury_counts['y'] = injury_counts['player_position'].map(lambda p: position_coords.get(str(p), (None, None))[1])

        # Hover-details
        details = (
            club_df.groupby("player_position")
            .agg({
                "player_name": lambda x: ", ".join(sorted(set(map(str, x)))),
                "Injury": lambda x: ", ".join(sorted(set(map(str, x))))
            })
            .reset_index()
        )

        injury_counts = injury_counts.merge(details, on="player_position", how="left")

        # Bubble-size
        injury_counts['bubble_size'] = injury_counts['injury_count']

        fig = go.Figure()

        fig.update_layout(
            plot_bgcolor="#6aa84f",
            paper_bgcolor="white",
            height=700,
            margin=dict(l=20, r=20, t=20, b=20)
        )

        shapes = [
            dict(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color="white", width=3)),  # soccer field
            dict(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color="white", width=3)),  # halfway line
            dict(type="circle", x0=50, y0=30, x1=70, y1=50, line=dict(color="white", width=3)),  # center circle
            dict(type="circle", x0=59, y0=39, x1=61, y1=41, line=dict(color="white", width=2), fillcolor="white"),  # center mark

            dict(type="rect", x0=0, y0=18, x1=18, y1=62, line=dict(color="white", width=3)),  # goal area left
            dict(type="rect", x0=102, y0=18, x1=120, y1=62, line=dict(color="white", width=3)),  # goal area right

            dict(type="rect", x0=0, y0=30, x1=6, y1=50, line=dict(color="white", width=3)),  # penalty area left
            dict(type="rect", x0=114, y0=30, x1=120, y1=50, line=dict(color="white", width=3)),  # penalty area right

            dict(type="circle", x0=10, y0=39, x1=12, y1=41, line=dict(color="white", width=2), fillcolor="white"),  # penalty mark left
            dict(type="circle", x0=108, y0=39, x1=110, y1=41, line=dict(color="white", width=2), fillcolor="white"),  # penalty mark right

            dict(type="path", path="M 18,32 Q 25,40 18,48", line_color="white",),  # penalty arc left
            dict(type="path", path="M 102,32 Q 95,40 102,48", line_color="white",),  # penalty arc right

            dict(type="path", path="M 0,76 Q 4,76 4,80", line_color="white",),  # corner arc top left
            dict(type="path", path="M 0,4 Q 4,4 4,0", line_color="white",),  # corner arc down left
            dict(type="path", path="M 120,76 Q 116,76 116,80", line_color="white",),  # corner arc top right
            dict(type="path", path="M 120,4 Q 116,4 116,0", line_color="white",),  # corner arc bottom right
        ]

        fig.update_layout(shapes=shapes)

        fig.add_trace(go.Scatter(
            x=injury_counts['x'],
            y=injury_counts['y'],
            mode="markers+text",
            text=injury_counts['injury_count'],
            textposition="middle center",
            textfont=dict(
                color="white",
                size=16
            ),
            marker=dict(
                size=injury_counts['bubble_size'],
                color="red",
                opacity=0.75,
                line=dict(color="black", width=2)
            ),
            customdata=injury_counts[['player_position', 'injury_count', 'player_name', 'Injury']],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Anzahl Verletzungen: %{customdata[1]}<br>"
                "Spieler: %{customdata[2]}<br>"
                "Verletzungen: %{customdata[3]}<extra></extra>"
            )
        ))

        # Labels
        for _, row in injury_counts.iterrows():
            fig.add_annotation(
                x=row['x'],
                y=row['y'] - 6,
                text=row['player_position'],
                showarrow=False,
                font=dict(size=11, color="white")
            )

        fig.update_xaxes(visible=False, range=[0, 120])
        fig.update_yaxes(visible=False, range=[0, 80], scaleanchor="x", scaleratio=1)

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Keine Daten für die aktuelle Club-/Liga-/Saison-Auswahl in der Kartenansicht verfügbar.")

with tab_bodymap:
    st.markdown("""
    ### 🏥 Für wen ist dieser Dashboard?
    **Zielgruppe:** Medizinisches Personal, Physiotherapeuten, Sportmediziner, Forscher
    
    **Was sieht man?**
    - Verletzungen nach Körperregion (Muskeln, Knie, Knöchel, etc.)
    - Anatomische Schwachpunkte im Kader pro Club
    - Häufigste Verletzungstypen nach Körperteil
    - Ressourcenallokation für Sportverletzungsbehandlung
    - Präventions- und Rehabilitations-Schwerpunkte
    """)
    st.divider()
    
    st.subheader("Interaktive Körperkarte")
    st.markdown("Analysiere die Verletzungen der Spieler durch ihre körperliche Position.")

    club_df = filtered_df.copy()
    if not club_df.empty:

        position_coords = {
            "Muscle": (45, 62),
            "Knee": (45, 42),
            "Ankle/Foot": (45, 14),
            "Back/Spine": (50, 94),
            "Head": (50, 124),
            "Shoulder": (34.5, 110.5),
        }

        club_df = club_df[club_df["injury_category"].isin(position_coords.keys())].copy()

        injury_counts = (
            club_df.groupby("injury_category")
            .agg(
                injury_count=("injury_category", "size"),
                player_name=("player_name", lambda x: ", ".join(sorted(set(x)))),
                injury_type=("Injury", lambda x: ", ".join(sorted(set(x))))
            )
            .reset_index()
        )

        injury_counts["x"] = injury_counts["injury_category"].map(lambda p: position_coords.get(str(p), (None, None))[0])
        injury_counts["y"] = injury_counts["injury_category"].map(lambda p: position_coords.get(str(p), (None, None))[1])

        fig = go.Figure()

        # -----------------------
        # Layout
        # -----------------------
        fig.update_layout(
            height=820,
            paper_bgcolor="#F8FAFC",
            plot_bgcolor="#F8FAFC",
            margin=dict(l=30, r=170, t=40, b=30),
            title=dict(
                text=f"Körperzonen mit Verletzungshäufung – {selected_club_global}",
                x=0.5,
                xanchor="center",
                font=dict(size=22, color="#0F172A")
            ),
            font=dict(
                family="Arial, sans-serif",
                color="#334155"
            ),
            xaxis=dict(
                visible=False,
                range=[0, 100],
                fixedrange=True
            ),
            yaxis=dict(
                visible=False,
                range=[0, 140],
                scaleanchor="x",
                scaleratio=1,
                fixedrange=True
            )
        )

        # -----------------------
        # Body silhouette
        # -----------------------
        body_line = dict(color="#94A3B8", width=2.2)
        body_fill = "#E2E8F0"

        shapes = [
            # Kopf
            dict(
                type="circle", x0=40, y0=114, x1=60, y1=134,
                line=body_line, fillcolor="#F8FAFC", layer="below"
            ),

            # Hals
            dict(
                type="rect", x0=46, y0=109, x1=54, y1=114,
                line=dict(color="rgba(0,0,0,0)"), fillcolor=body_fill, layer="below"
            ),

            # Oberkörper
            dict(
                type="path",
                path="M 35 108 Q 34 92 35 72 L 65 72 Q 66 92 65 108 Q 58 114 50 114 Q 42 114 35 108 Z",
                line=body_line, fillcolor=body_fill, layer="below"
            ),

            # Arm links
            dict(
                type="path",
                path="M 35 106 Q 29 101 28 94 L 28 60 Q 28 57 31 57 L 35 57 L 35 106 Z",
                line=body_line, fillcolor="#EEF2F7", layer="below"
            ),

            # Arm rechts
            dict(
                type="path",
                path="M 65 106 Q 71 101 72 94 L 72 60 Q 72 57 69 57 L 65 57 L 65 106 Z",
                line=body_line, fillcolor="#EEF2F7", layer="below"
            ),

            # Hüfte
            dict(
                type="path",
                path="M 40 72 L 60 72 L 58 64 L 42 64 Z",
                line=body_line, fillcolor="#CBD5E1", layer="below"
            ),

            # Bein links
            dict(
                type="path",
                path="M 42 64 L 49 64 L 49 20 L 40 20 L 40 58 Q 40 62 42 64 Z",
                line=body_line, fillcolor="#EEF2F7", layer="below"
            ),

            # Bein rechts
            dict(
                type="path",
                path="M 51 64 L 58 64 L 60 58 L 60 20 L 51 20 Z",
                line=body_line, fillcolor="#EEF2F7", layer="below"
            ),

            # Knie links
            dict(
                type="circle", x0=40, y0=39, x1=49, y1=48,
                line=body_line, fillcolor="#F8FAFC", layer="below"
            ),

            # Knie rechts
            dict(
                type="circle", x0=51, y0=39, x1=60, y1=48,
                line=body_line, fillcolor="#F8FAFC", layer="below"
            ),

            # Fuß links
            dict(
                type="path",
                path="M 38 20 L 50 20 L 50 10 L 36 10 L 36 16 Q 36 20 38 20 Z",
                line=body_line, fillcolor="#DCE3EA", layer="below"
            ),

            # Fuß rechts
            dict(
                type="path",
                path="M 50 20 L 62 20 Q 64 20 64 18 L 64 10 L 50 10 Z",
                line=body_line, fillcolor="#DCE3EA", layer="below"
            ),
        ]

        fig.update_layout(shapes=shapes)

        # -----------------------
        # Legende links unten als Annotationen
        # -----------------------
        legend_items = [
            ("Bänder", "#2563EB"),
            ("Knochen", "#F59E0B"),
            ("Illness", "#7C3AED"),
            ("Non-Injury", "#16A34A"),
            ("Minor", "#EAB308"),
        ]

        legend_x = 77
        legend_y_start = 112
        gap = 10

        fig.add_annotation(
            x=legend_x,
            y=legend_y_start + 10,
            text="<b>Kategorien</b>",
            showarrow=False,
            xanchor="left",
            font=dict(size=14, color="#0F172A")
        )

        for i, (label, color) in enumerate(legend_items):
            y = legend_y_start - i * gap

            fig.add_shape(
                type="rect",
                x0=legend_x,
                y0=y - 2.5,
                x1=legend_x + 4,
                y1=y + 2.5,
                line=dict(color="rgba(0,0,0,0)"),
                fillcolor=color
            )

            fig.add_annotation(
                x=legend_x + 5.5,
                y=y,
                text=label,
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                font=dict(size=12, color="#475569")
            )

        # -----------------------
        # Marker-Styling
        # -----------------------
        min_count = injury_counts["injury_count"].min()
        max_count = injury_counts["injury_count"].max()

        def label_color(v, vmin, vmax):
            if vmax == vmin:
                return "#FFFFFF"
            threshold = vmin + (vmax - vmin) * 0.55
            return "#FFFFFF" if v >= threshold else "#111827"

        injury_counts["text_color"] = injury_counts["injury_count"].apply(
            lambda v: label_color(v, min_count, max_count)
        )

        hover_custom = injury_counts[["injury_category", "injury_count", "player_name", "injury_type"]]

        fig.add_trace(go.Scatter(
            x=injury_counts["x"],
            y=injury_counts["y"],
            mode="markers+text",
            text=injury_counts["injury_count"],
            textposition="middle center",
            customdata=hover_custom,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Anzahl: %{customdata[1]}<br>"
                "Spieler: %{customdata[2]}<br>"
                "Typ: %{customdata[3]}<extra></extra>"
            ),
            marker=dict(
                size=36,
                color=injury_counts["injury_count"],
                colorscale=[
                    [0.0, "#FEE2E2"],
                    [0.25, "#FCA5A5"],
                    [0.5, "#F87171"],
                    [0.75, "#DC2626"],
                    [1.0, "#7F1D1D"]
                ],
                cmin=min_count,
                cmax=max_count,
                line=dict(color="#FFFFFF", width=2.5),
                showscale=True,
                colorbar=dict(
                    title="Anzahl",
                    thickness=12,
                    len=0.42,
                    y=0.28,
                    x=1.02,
                    outlinewidth=0,
                #  tickfont=dict(size=11, color="#475569"),
                #  titlefont=dict(size=12, color="#334155")
                ),
                opacity=0.97
            ),
            textfont=dict(
                size=15,
                color=injury_counts["text_color"],
                family="Arial, sans-serif"
            ),
            showlegend=False
        ))

        # Optional: dezente Unterzeile
        fig.add_annotation(
            x=50,
            y=2.5,
            text="Grössere/dunklere Marker zeigen häufiger registrierte Verletzungen pro Körperzone",
            showarrow=False,
            font=dict(size=12, color="#64748B"),
            xanchor="center"
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Keine Daten für die aktuelle Club-/Liga-/Saison-Auswahl in der Körperkarte verfügbar.")
        

with tab_dddm:
    def season_start_year(season: str) -> int:
        try:
            return int(str(season).split("/")[0])
        except (ValueError, IndexError):
            return 9999

    def checkSeason():
        if any(season_start_year(season) < season_start_year(DEFAULT_SEASON) for season in selected_seasons):
            return st.warning(
                "Du hast ältere Saisons als 24/25 ausgewählt. Die Kaderzusammensetzung kann dadurch vom aktuellen Kader abweichen, "
                "weil Transfers, Abgänge und Neuzugänge nicht mehr exakt dem heutigen Team entsprechen."
            , icon="⚠️")
        
    st.markdown("""
    ### 💼 Für wen ist dieser Dashboard?
    **Zielgruppe:** Club-Führung, Geschäftsführer, Sportdirektor, CFO, Contract Manager
    
    **Was sieht man?**
    - **Finanzielle Risikobewertung:** Marktwert vs. Verletzungshäufigkeit pro Spieler
    - **Squad-Wertanalyse:** Gesamte Kader-Risikoexposition in Echtgeld
    - **Vertragsentscheidungen:** Investitionsrisiken für Verlängerungen
    - **Ressourcenplanung:** Budget-Allokation für Medizin und Prävention
    - **Capital Project Appraisal (CPA):** ROI von medizinischen Investitionen
    - **Strategische HR-Entscheidungen:** Spielertransfers, Versicherung, Vertragsstrukturen
    """)
    st.divider()

    st.subheader("🧭 Methodik & Entscheidungsgrundsatz")
    st.markdown("""
    Dieser Tab folgt dem Grundsatz: **sportliches Risiko in finanzielle Auswirkungen übersetzen**, damit Verträge,
    Budget und Kaderstruktur datenbasiert entschieden werden.

    **Zentrale Logik:**
    1. Historische Ausfalltage messen die Verfügbarkeit.
    2. Marktwert quantifiziert die finanzielle Relevanz eines Spielers.
    3. Aus beiden wird ein monetärer Risikoindikator berechnet.
    """)

    with st.expander("Wie wird gerechnet und warum ist das relevant?", expanded=False):
        st.markdown("""
        **A) Spielerbezogene Risikoanalyse (bei aktiver Spielersuche)**

        - **Gesamtausfalltage** = Summe aller `Days` des Spielers in der gewählten Filterung.
        - **Anzahl Verletzungen** = Anzahl der Verletzungsereignisse.
        - **Marktwert** = `market_value_in_eur` als finanzielle Basisgröße.

        **Finanzielle Übersetzung:**
        - Es wird ein 5-Jahres-Horizont angenommen (`career_years = 5`).
        - **Daily Opportunity Cost** = Marktwert / (5 * 365)
        - **Kapitalverlust durch Ausfalltage** = Daily Opportunity Cost * Gesamtausfalltage
        - **Risiko in % des Marktwerts** = Gesamtausfalltage / (5 * 365) * 100

        **Warum sinnvoll?**
        - Verletzungstage werden in eine einheitliche Währung (EUR) überführt.
        - Verträge können auf Basis von "Wert bei Verfügbarkeit" statt nur Bauchgefühl bewertet werden.

        **B) Budget-/Präventionsanalyse (Medical Budget)**

        - Verletzungstypen werden nach **Total_Days** aggregiert.
        - Die höchsten Total_Days markieren die größten produktiven und finanziellen Belastungstreiber.

        **Warum sinnvoll?**
        - Präventionsbudget fließt zuerst in Verletzungstypen mit dem höchsten erwarteten ROI.

        **C) Kader-Wertanalyse / Squad Vulnerability (ohne aktive Spielersuche)**

        Pro Spieler werden berechnet:
        - `Total_Days`, `Injury_Count`, `Market_Value`
        - **Financial_Risk_EUR** = (Market_Value / (5 * 365)) * Total_Days
        - **Risk_Percentage** = Total_Days / (5 * 365) * 100

        Danach wird auf Kaderlevel aggregiert:
        - Gesamtmarktwert
        - Gesamtes Verletzungsrisiko (EUR)
        - Ø Risiko pro Spieler
        - Anteil Hochrisikospieler (>100 Ausfalltage)

        **Warum sinnvoll?**
        - Der Kader wird als Portfolio betrachtet: Konzentrationsrisiken werden sichtbar.
        - Hohe Wertbindung bei hoher Ausfallanfälligkeit wird früh erkannt.

        **D) Entscheidungsregel als Grundsatz**

        - **Vertrag:** Je höher Financial_Risk_EUR und Risk_Percentage, desto defensiver Vertragsstruktur (Laufzeit, Bonuslogik, Absicherung).
        - **Kaderplanung:** Bei hoher Hochrisikospieler-Quote Backups/Rotation gezielt ausbauen.
        - **Budget:** Prävention dort priorisieren, wo der größte Risikoabbau pro investiertem Euro erwartet wird.
        - **Risikotragfähigkeit:** Gesamtrisikoquote des Kaders als Steuergröße für Transfer- und Versicherungsstrategie nutzen.
        """)
    st.divider()
    
    st.subheader("📊 DDDM: Risikoanalyse für Kadermanagement")
    st.markdown("""
    **Anwendungsfall:** Soll der Vertrag eines Spielers verlängert werden?
    Diese prädiktive Metrik berechnet einen Risiko-Score basierend auf historischen Ausfalltagen, um finanzielle Fehlinvestitionen zu vermeiden.
    """)
    
    if player_search and not filtered_df.empty:
        checkSeason()
        player_data = filtered_df[filtered_df['player_name'].str.contains(player_search, case=False, na=False)]

        if not player_data.empty:
            total_days_missed = player_data['Days'].sum()
            total_injuries = len(player_data)
            market_value = player_data['market_value_in_eur'].iloc[0] if pd.notna(player_data['market_value_in_eur'].iloc[0]) else 0

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
                st.metric("Marktwert", f"€{market_value:,.0f}".replace(",", "."))
                st.info(f"**Kalkuliertes Investment-Risiko:** {risk_level}")
                st.warning(action_recommendation)

            # Financial Risk Impact
            st.divider()
            st.subheader("💰 Finanzielle Risikoauswirkung")
            
            # Calculate daily opportunity cost based on market value
            career_years = 5  # typical remaining career value assumption
            daily_opportunity_cost = market_value / (career_years * 365)
            total_financial_impact = daily_opportunity_cost * total_days_missed
            
            risk_percentage = (total_days_missed / (career_years * 365)) * 100
            
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                st.metric(
                    "Kapitalverlust (Ausfalltage)",
                    f"€{total_financial_impact:,.0f}".replace(",", "."),
                    f"{risk_percentage:.1f}% des Marktwerts"
                )
            
            with f_col2:
                avg_days_per_injury = total_days_missed / total_injuries if total_injuries > 0 else 0
                st.metric("Ø Ausfalltage pro Verletzung", f"{avg_days_per_injury:.1f}")
            
            with f_col3:
                annual_impact = (total_days_missed / ((player_data['Season'].nunique()) or 1)) * daily_opportunity_cost
                st.metric(
                    "Ø Jahresauswirkung",
                    f"€{annual_impact:,.0f}".replace(",", ".")
                )

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
        checkSeason()
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

    st.divider()
    st.subheader("🎯 DDDM: Kader-Wertanalyse & Squad Vulnerability Assessment")
    st.markdown("""
    **Anwendungsfall:** Welche Spieler im Kader stellen ein hohes finanzielles Risiko dar?
    Diese Analyse kombiniert Marktwert mit Verletzungshistorie, um die finanzielle Anfälligkeit des Kaders zu bewerten.
    """)

    # Only show squad analysis when no specific player is searched
    if not player_search:
        checkSeason()
        club_filtered_df = filtered_df.copy()
        
        if not club_filtered_df.empty:
            # Group by player and calculate aggregate metrics
            player_valuation = club_filtered_df.groupby('player_name').agg(
                Total_Days=('Days', 'sum'),
                Injury_Count=('player_name', 'count'),
                Market_Value=('market_value_in_eur', 'first'),
                League=('league', 'first'),
                Position=('player_position', 'first')
            ).reset_index()

            # Remove players without market value
            player_valuation = player_valuation[player_valuation['Market_Value'].notna() & (player_valuation['Market_Value'] > 0)]
            
            if not player_valuation.empty:
                # Calculate risk metrics
                career_years = 5
                player_valuation['Daily_Opportunity_Cost'] = player_valuation['Market_Value'] / (career_years * 365)
                player_valuation['Financial_Risk_EUR'] = player_valuation['Daily_Opportunity_Cost'] * player_valuation['Total_Days']
                player_valuation['Risk_Percentage'] = (player_valuation['Total_Days'] / (career_years * 365) * 100).round(2)
                
                # Sort by financial risk
                player_valuation_sorted = player_valuation.sort_values('Financial_Risk_EUR', ascending=False)
                
                # Top 10 highest financial risk players
                st.subheader("🚨 Die 10 finanziell riskantesten Spieler")
                
                top_risk = player_valuation_sorted.head(10)[['player_name', 'Market_Value', 'Total_Days', 'Injury_Count', 'Financial_Risk_EUR', 'Risk_Percentage']].copy()
                top_risk.columns = ['Spieler', 'Marktwert (€)', 'Ausfalltage', 'Verletzungen', 'Finanz. Risiko (€)', 'Risiko %']
                
                # Format columns for display
                top_risk['Marktwert (€)'] = top_risk['Marktwert (€)'].apply(lambda x: f"€{x:,.0f}".replace(",", "."))
                top_risk['Finanz. Risiko (€)'] = top_risk['Finanz. Risiko (€)'].apply(lambda x: f"€{x:,.0f}".replace(",", "."))
                
                st.dataframe(top_risk, use_container_width=True, hide_index=True)
                
                # Scatter plot: Market Value vs Injury Risk
                st.subheader("📈 Marktwert vs. Verletzungsrisiko (Squad-Portefeuilleansicht)")
                
                fig_scatter = px.scatter(
                    player_valuation,
                    x='Market_Value',
                    y='Total_Days',
                    size='Injury_Count',
                    color='Financial_Risk_EUR',
                    hover_data=['player_name', 'League', 'Position', 'Risk_Percentage'],
                    labels={
                        'Market_Value': 'Marktwert (€)',
                        'Total_Days': 'Gesamtausfalltage',
                        'Injury_Count': 'Anz. Verletzungen',
                        'Financial_Risk_EUR': 'Finanzielles Risiko (€)'
                    },
                    title="Squad-Portfolio: Welche hochbewerteten Spieler gefährden den finanziellen Erfolg?",
                    color_continuous_scale='Reds'
                )
                fig_scatter.add_hline(
                    y=player_valuation['Total_Days'].median(),
                    line_dash="dash",
                    annotation_text=f"Median: {player_valuation['Total_Days'].median():.0f} Tage",
                    annotation_position="right"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Financial impact summary
                st.subheader("💼 Gesamte Kader-Risikoexposition")
                
                total_market_value = player_valuation['Market_Value'].sum()
                total_financial_risk = player_valuation['Financial_Risk_EUR'].sum()
                avg_risk_per_player = player_valuation['Financial_Risk_EUR'].mean()
                high_risk_count = len(player_valuation[player_valuation['Total_Days'] > 100])
                
                sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
                with sum_col1:
                    st.metric(
                        "Gesamter Kader-Marktwert",
                        f"€{total_market_value:,.0f}".replace(",", ".")
                    )
                with sum_col2:
                    st.metric(
                        "Gesamtes Verletzungsrisiko",
                        f"€{total_financial_risk:,.0f}".replace(",", "."),
                        f"{(total_financial_risk/total_market_value*100):.1f}% des Marktwerts"
                    )
                with sum_col3:
                    st.metric(
                        "Ø Risiko pro Spieler",
                        f"€{avg_risk_per_player:,.0f}".replace(",", ".")
                    )
                with sum_col4:
                    st.metric(
                        "Hochrisikospieler (>100 Tage)",
                        high_risk_count
                    )
                
                # Strategic Insights
                st.divider()
                st.subheader("🎲 Strategische Einsichten für das Management")
                
                left_insight, right_insight = st.columns(2)
                
                with left_insight:
                    st.markdown("**Squad-Diversifikation:**")
                    if high_risk_count / len(player_valuation) > 0.3:
                        st.warning(f"""
                        ⚠️ **{(high_risk_count/len(player_valuation)*100):.0f}%** des Kaders sind Hochrisikoträger.
                        
                        **Handlung:** Wertvolle Backups für diese Positionen nachdenken über Verstärkung.
                        """)
                    else:
                        st.success(f"""
                        ✓ Gutes Risiko-Management ({(high_risk_count/len(player_valuation)*100):.0f}% Hochrisikoträger).
                        """)
                
                with right_insight:
                    st.markdown("**Finanzielle Resilienz:**")
                    risk_ratio = (total_financial_risk / total_market_value * 100)
                    if risk_ratio > 15:
                        st.error(f"""
                        🔴 **{risk_ratio:.1f}%** des Marktwerts ist durch Verletzungsrisiko gefährdet.
                        
                        **Handlung:** Versicherungen, Belastungsmanagement oder Vertragsbewertung überprüfen.
                        """)
                    elif risk_ratio > 8:
                        st.warning(f"""
                        🟡 **{risk_ratio:.1f}%** Risiko-Quote. Moderates Expositionsniveau.
                        """)
                    else:
                        st.success(f"""
                        🟢 **{risk_ratio:.1f}%** Risiko-Quote. Niedriges Expositionsniveau.
                        """)
            else:
                st.info("Keine Marktwertdaten für die Risikoanalyse verfügbar.")
        else:
            st.info("Keine Daten für den ausgewählten Club verfügbar.")
    else:
        st.info("Die Squad-Wertanalyse ist aufgrund einer aktiven Spielersuche nicht verfügbar. Bitte leere die Suchfeld, um die Club-Kader-Analyse zu sehen.")

    st.markdown("---")