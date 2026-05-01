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
    df['injury_until_parsed'] = pd.to_datetime(df['injury_until_parsed'], errors='coerce') # Ensure this exists
    df['Month'] = df['injury_from_parsed'].dt.month_name(locale="de_DE.UTF-8")
    df['Month_Num'] = df['injury_from_parsed'].dt.month
    return df

@st.cache_data
def load_valuation_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    val_path = os.path.join(script_dir, "../Data/player_valuations.csv")
    players_path = os.path.join(script_dir, "../Data/players.csv")
    
    # Load valuations
    val_df = pd.read_csv(val_path)
    val_df['date'] = pd.to_datetime(val_df['date'])
    
    # Load player names for mapping
    players_df = pd.read_csv(players_path)
    players_df = players_df[['player_id', 'name']]
    
    # Join
    merged_val = pd.merge(val_df, players_df, on='player_id', how='left')
    return merged_val

@st.cache_data
def load_players_full():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    players_path = os.path.join(script_dir, "../Data/players.csv")
    players_df = pd.read_csv(players_path)
    return players_df

@st.cache_data(show_spinner=False)
def load_tournament_players():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        events_path = os.path.join(script_dir, "../Data/game_events.csv")
        games_path = os.path.join(script_dir, "../Data/games.csv")
        players_path = os.path.join(script_dir, "../Data/players.csv")

        df_events = pd.read_csv(events_path, usecols=['game_id', 'player_id'])
        df_games = pd.read_csv(games_path, usecols=['game_id', 'competition_id', 'season'])
        df_players = pd.read_csv(players_path, usecols=['player_id', 'name'])

        euro2020_games = df_games[(df_games['competition_id'] == 'EURO') & (df_games['season'] == 2020)]['game_id'].unique()
        wm2022_games = df_games[df_games['competition_id'] == 'FIWC']['game_id'].unique()
        euro2024_games = df_games[(df_games['competition_id'] == 'EURO') & (df_games['season'] == 2023)]['game_id'].unique()

        euro2020_pids = df_events[df_events['game_id'].isin(euro2020_games)]['player_id'].dropna().unique()
        wm2022_pids = df_events[df_events['game_id'].isin(wm2022_games)]['player_id'].dropna().unique()
        euro2024_pids = df_events[df_events['game_id'].isin(euro2024_games)]['player_id'].dropna().unique()

        euro2020_names = set(df_players[df_players['player_id'].isin(euro2020_pids)]['name'].unique())
        wm2022_names = set(df_players[df_players['player_id'].isin(wm2022_pids)]['name'].unique())
        euro2024_names = set(df_players[df_players['player_id'].isin(euro2024_pids)]['name'].unique())

        return euro2020_names, wm2022_names, euro2024_names
    except Exception as e:
        return set(), set(), set()

def get_injury_color(category, injury_name):
    cat = str(category).lower()
    inj = str(injury_name).lower()
    
    # Rot (Trauma/Struktur)
    if any(x in cat for x in ['knee', 'ankle', 'foot', 'shoulder']) or \
       any(x in inj for x in ['fracture', 'torn', 'break', 'rupture', 'ligament']):
        return "red"
    
    # Orange (Muskulär)
    if 'muscle' in cat or any(x in inj for x in ['hamstring', 'adductor', 'muscle', 'fibers', 'strain']):
        return "orange"
        
    # Gelb (Krankheit)
    if 'illness' in cat or any(x in inj for x in ['illness', 'internal', 'cold', 'flu', 'infection']):
        return "yellow"
        
    # Grau (Andere)
    return "grey"

@st.cache_data
def load_clubs():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    clubs_path = os.path.join(script_dir, "../Data/clubs.csv")
    clubs_df = pd.read_csv(clubs_path)
    return clubs_df

df = load_data()
val_df = load_valuation_data()
players_info_df = load_players_full()
clubs_info_df = load_clubs()

DEFAULT_SEASON = "24/25"
club_options = ["Alle Clubs"] + sorted(df['club'].dropna().unique().tolist())
season_options = sorted(df['Season'].dropna().unique().tolist())
TOURNAMENT_OPTIONS = [
    "Alle Spieler (Kein Filter)", 
    "EURO 2020 (11.06. - 11.07.2021)", 
    "WM 2022 (20.11. - 18.12.2022)", 
    "EURO 2024 (14.06. - 14.07.2024)", 
    "WM und EM (Alle 3 Turniere)", 
    "Keine Turnierteilnahme"
]

# --- Initialize Session State ---
if 'filter_club' not in st.session_state:
    st.session_state['filter_club'] = "Alle Clubs"
if 'filter_leagues' not in st.session_state:
    st.session_state['filter_leagues'] = sorted(df['league'].dropna().unique().tolist())
if 'filter_seasons' not in st.session_state:
    st.session_state['filter_seasons'] = [DEFAULT_SEASON] if DEFAULT_SEASON in season_options else season_options
if 'filter_players' not in st.session_state:
    st.session_state['filter_players'] = []

# --- Global Filter UI ---
# Globale Filter auskommentiert laut Anforderung
# with st.expander("🌍 Globale Filter (Club & Saison)", expanded=False):
#     col1, col2 = st.columns(2)
#     with col1:
#         selected_club_global = st.selectbox(
#             "Club auswählen",
#             club_options,
#             key='filter_club',
#             help="Dieser globale Filter gilt für alle Dashboards."
#         )
#     with col2:
#         selected_seasons = st.multiselect(
#             "Saisons auswählen", 
#             season_options, 
#             key='filter_seasons'
#         )
#         if not selected_seasons:
#             selected_seasons = [DEFAULT_SEASON] if DEFAULT_SEASON in season_options else season_options
#             st.session_state['filter_seasons'] = selected_seasons

selected_club_global = "Alle Clubs"
selected_seasons = season_options

# League Filter (depends on selected club)
if selected_club_global == "Alle Clubs":
    league_options = sorted(df['league'].dropna().unique().tolist())
else:
    league_options = sorted(df.loc[df['club'] == selected_club_global, 'league'].dropna().unique().tolist())

st.session_state['filter_leagues'] = [l for l in st.session_state['filter_leagues'] if l in league_options]
if not st.session_state['filter_leagues']:
    st.session_state['filter_leagues'] = league_options

selected_leagues = league_options # Default to all leagues since filter is disabled

# Player Search (limited to selected club and other active filters)
st.sidebar.markdown("---")

min_date = df['injury_from_parsed'].min().date()
max_date = df['injury_from_parsed'].max().date()

# date_range = st.sidebar.date_input(
#     "Zeitraum (Verletzungsbeginn)",
#     value=(min_date, max_date),
#     min_value=min_date,
#     max_value=max_date,
#     help="Filtert Verletzungen basierend auf dem Datum, an dem sie passiert sind."
# )
if 'date_range' not in st.session_state:
    st.session_state['date_range'] = (min_date, max_date)
date_range = st.session_state['date_range']
st.sidebar.markdown("---")

# tournament_filter = st.sidebar.radio(
#     "Turnier-Teilnahme Filter",
#     options=["Alle Spieler (Kein Filter)", "Europameisterschaft (EM)", "Weltmeisterschaft (WM)", "WM und EM", "Keine Turnierteilnahme"],
#     help="Filtert die Spieler anhand ihrer dokumentierten WM/EM-Teilnahme."
# )
if 'tournament_filter' not in st.session_state:
    st.session_state['tournament_filter'] = "Alle Spieler (Kein Filter)"
tournament_filter = st.session_state['tournament_filter']

st.sidebar.markdown("---")

player_source_df = df.copy()
if selected_club_global != "Alle Clubs":
    player_source_df = player_source_df[player_source_df['club'] == selected_club_global]
if selected_leagues:
    player_source_df = player_source_df[player_source_df['league'].isin(selected_leagues)]
if selected_seasons:
    player_source_df = player_source_df[player_source_df['Season'].isin(selected_seasons)]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_dt = pd.to_datetime(date_range[0])
    end_dt = pd.to_datetime(date_range[1])
    player_source_df = player_source_df[
        (player_source_df['injury_from_parsed'] >= start_dt) & 
        (player_source_df['injury_from_parsed'] <= end_dt)
    ]

if tournament_filter != "Alle Spieler (Kein Filter)":
    e20, w22, e24 = load_tournament_players()
    if "EURO 2020" in tournament_filter:
        player_source_df = player_source_df[player_source_df['player_name'].isin(e20)]
    elif "WM 2022" in tournament_filter:
        player_source_df = player_source_df[player_source_df['player_name'].isin(w22)]
    elif "EURO 2024" in tournament_filter:
        player_source_df = player_source_df[player_source_df['player_name'].isin(e24)]
    elif "WM und EM" in tournament_filter:
        player_source_df = player_source_df[player_source_df['player_name'].isin(e20.union(w22).union(e24))]
    elif "Keine Turnierteilnahme" in tournament_filter:
        all_tournament_players = e20.union(w22).union(e24)
        player_source_df = player_source_df[~player_source_df['player_name'].isin(all_tournament_players)]

player_options = sorted(player_source_df['player_name'].dropna().unique().tolist())
st.session_state['filter_players'] = [p for p in st.session_state['filter_players'] if p in player_options]

# player_searchBox = st.sidebar.multiselect(
#     "Spieler suchen",
#     options=player_options,
#     key='filter_players',
#     max_selections=1,
#     help="Suche ist auf die aktiven Filter begrenzt."
# )
# player_search = player_searchBox[0] if player_searchBox else ""
if 'player_search' not in st.session_state:
    st.session_state['player_search'] = ""
player_search = st.session_state['player_search']

st.sidebar.markdown("---")
st.sidebar.caption("Navigation erfolgt über Tabs im Hauptbereich.")

# Filter Data
filtered_df = df[
    (df['league'].isin(selected_leagues)) &
    (df['Season'].isin(selected_seasons))
]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_dt = pd.to_datetime(date_range[0])
    end_dt = pd.to_datetime(date_range[1])
    filtered_df = filtered_df[
        (filtered_df['injury_from_parsed'] >= start_dt) & 
        (filtered_df['injury_from_parsed'] <= end_dt)
    ]

if selected_club_global != "Alle Clubs":
    filtered_df = filtered_df[filtered_df['club'] == selected_club_global]

if player_search:
    filtered_df = filtered_df[filtered_df['player_name'].str.contains(player_search, case=False, na=False)]

if tournament_filter != "Alle Spieler (Kein Filter)":
    e20, w22, e24 = load_tournament_players()
    if "EURO 2020" in tournament_filter:
        filtered_df = filtered_df[filtered_df['player_name'].isin(e20)]
    elif "WM 2022" in tournament_filter:
        filtered_df = filtered_df[filtered_df['player_name'].isin(w22)]
    elif "EURO 2024" in tournament_filter:
        filtered_df = filtered_df[filtered_df['player_name'].isin(e24)]
    elif "WM und EM" in tournament_filter:
        filtered_df = filtered_df[filtered_df['player_name'].isin(e20.union(w22).union(e24))]
    elif "Keine Turnierteilnahme" in tournament_filter:
        all_tournament_players = e20.union(w22).union(e24)
        filtered_df = filtered_df[~filtered_df['player_name'].isin(all_tournament_players)]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Gesamtverletzungen", f"{len(filtered_df):,}".replace(",", "."))
col2.metric("Ausfalltage insgesamt", f"{filtered_df['Days'].sum():,}".replace(",", "."))
col3.metric("Ø Tage pro Verletzung", f"{filtered_df['Days'].mean():.1f}".replace(".", ",") if len(filtered_df) > 0 else "0")
col4.metric("Ø Verpasste Spiele", f"{filtered_df['Games missed'].mean():.1f}".replace(".", ",") if len(filtered_df) > 0 else "0")

if filtered_df.empty:
    st.warning("Keine Daten für die gewählten Filter. Bitte passe Liga, Saison oder Spieler an.")

# Tab Labels
tab_labels = [
    # "Übersicht",
    # "Verletzungsvergleich",
    "Zeit & Liga",
    # "Tabellen",
    "Karten",    
    "Bodymap",
    "DDDM Entscheidungen",
    "Marktwert & Risiko-Analyse"
]

# Ensure active_tab is in session state and handle redirection
if "tab" in st.query_params:
    st.session_state["active_dashboard_tab"] = st.query_params["tab"]
elif "requested_tab" in st.session_state:
    st.session_state["active_dashboard_tab"] = st.session_state["requested_tab"]
    del st.session_state["requested_tab"]

if "active_dashboard_tab" not in st.session_state:
    st.session_state["active_dashboard_tab"] = "Zeit & Liga"

def update_tab_url():
    """Updates the URL query parameters when a tab is clicked."""
    st.query_params["tab"] = st.session_state["active_dashboard_tab"]

# tab_overview, tab_injuries, tab_trends, tab_tables, tap_maps, tab_bodymap, tab_dddm, tab_market_risk = st.tabs(
# tab_trends, tab_tables, tap_maps, tab_bodymap, tab_dddm, tab_market_risk = st.tabs(
tab_trends, tap_maps, tab_bodymap, tab_dddm, tab_market_risk = st.tabs(
    tab_labels, 
    key="active_dashboard_tab",
    on_change=update_tab_url
)


# with tab_overview:
if False:
    st.markdown("""
    ### 📊 Für wen ist dieses Dashboard?
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

# with tab_injuries:
if False:
    st.markdown("""
    ### 🏥 Für wen ist dieses Dashboard?
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
    all_injuries = sorted(filtered_df['Injury'].dropna().unique().tolist())
    selected_injury = st.selectbox("Verletzung auswählen", all_injuries, help="Wähle eine Verletzung aus, um den Vergleich zu starten.")

    if selected_injury:
        inj_df = filtered_df[filtered_df['Injury'] == selected_injury].copy()
        
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
    ### 📈 Für wen ist dieses Dashboard?
    **Zielgruppe:** Strategische Planer, Team-Manager, Athletik-Trainer, Forscher
    
    **Was sieht man?**
    - Saisonale und monatliche Verletzungsmuster
    - Vergleich von Verletzungstrends zwischen verschiedenen Ligen
    - Jahresüber-Vergleiche und historische Entwicklungen
    - Identifikation von Peak-Monaten für Verletzungen
    - Planung von Präventions- und Trainingsprogrammen basierend auf Saisonalität
    """)
    st.divider()
    
    # --- New Comparison Logic ---
    st.subheader("🏆 Verletzungsverlauf")
    st.markdown("Vergleiche Turnierteilnehmer (WM/EM) mit Kontrollgruppen oder anderen Turnieren.")
    
    with st.expander("⚙️ Vergleichskonfiguration (Vergleich vs. Kontrolle)", expanded=True):
        c1, c2 = st.columns(2)
        
        league_options_all = sorted(df['league'].dropna().unique().tolist())
        
        with c1:
            st.markdown("**1. Vergleichswerte (Gruppe A)**")
            v_tournament = st.selectbox(
                "Turnierfilter (A)",
                options=TOURNAMENT_OPTIONS,
                index=2, # Default to WM
                key="v_group_tournament"
            )
            v_leagues = st.multiselect("Ligen (A)", league_options_all, default=league_options_all, key="v_group_leagues")
            v_season = st.multiselect("Saison (A)", season_options, default=season_options, key="v_group_season")
            
        with c2:
            st.markdown("**2. Kontrollwerte (Gruppe B)**")
            k_tournament = st.selectbox(
                "Turnierfilter (B)",
                options=TOURNAMENT_OPTIONS,
                index=5, # Default to Keine Turnierteilnahme
                key="k_group_tournament"
            )
            k_leagues = st.multiselect("Ligen (B)", league_options_all, default=league_options_all, key="k_group_leagues")
            k_season = st.multiselect("Saison (B)", season_options, default=season_options, key="k_group_season")

        st.markdown("---")
        use_randomizer = st.checkbox(
            "🎲 Äquivalenzgruppe (Stratified Matching): Kontrollgruppe B an Liga und Position von Gruppe A spiegeln", 
            value=True,
            help="Zieht für Gruppe B exakt dieselbe Anzahl an Spielern mit der gleichen Ligen- und Positions-Verteilung wie in Gruppe A."
        )

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

    import random
    all_players_base = players_info_df['name'].dropna().unique()
    
    players_a = list(get_tournament_players(v_tournament, all_players_base))
    players_b_pool = list(get_tournament_players(k_tournament, all_players_base))
    players_b = players_b_pool.copy()

    # Apply Stratified Matching Randomizer
    n_a = len(players_a)
    if use_randomizer and n_a > 0:
        if len(players_b_pool) > n_a:
            seed_str = f"{v_tournament}_{k_tournament}_{''.join(v_season)}_{''.join(k_season)}"
            random.seed(hash(seed_str))
            
            # DataFrame representation for Stratified Sampling
            df_a_info = players_info_df[players_info_df['name'].isin(players_a)].copy()
            df_b_info = players_info_df[players_info_df['name'].isin(players_b_pool)].copy()
            
            # Remove duplicate names to ensure exact counts
            df_a_info = df_a_info.drop_duplicates(subset=['name'])
            df_b_info = df_b_info.drop_duplicates(subset=['name'])
            
            # Fill NA to avoid grouping issues
            df_a_info['current_club_domestic_competition_id'] = df_a_info['current_club_domestic_competition_id'].fillna('Unknown')
            df_a_info['position'] = df_a_info['position'].fillna('Unknown')
            df_b_info['current_club_domestic_competition_id'] = df_b_info['current_club_domestic_competition_id'].fillna('Unknown')
            df_b_info['position'] = df_b_info['position'].fillna('Unknown')
            
            # Calculate strata distribution in A
            strata_counts = df_a_info.groupby(['current_club_domestic_competition_id', 'position']).size().to_dict()
            
            sampled_b_names = []
            
            # Sample for each stratum
            for (league, pos), count in strata_counts.items():
                pool_for_stratum = df_b_info[(df_b_info['current_club_domestic_competition_id'] == league) & (df_b_info['position'] == pos)]['name'].tolist()
                
                if len(pool_for_stratum) >= count:
                    sampled_b_names.extend(random.sample(pool_for_stratum, count))
                else:
                    sampled_b_names.extend(pool_for_stratum)
                    
            # Fallback if we didn't reach n_a
            remaining_needed = n_a - len(sampled_b_names)
            if remaining_needed > 0:
                remaining_pool = list(set(players_b_pool) - set(sampled_b_names))
                if len(remaining_pool) >= remaining_needed:
                    sampled_b_names.extend(random.sample(remaining_pool, remaining_needed))
                else:
                    sampled_b_names.extend(remaining_pool)
                    
            players_b = sampled_b_names

    # Construct Comparison Data (Filtering the injuries dataframe based on the player populations)
    df_a = df[df['player_name'].isin(players_a)].copy()
    if v_leagues: df_a = df_a[df_a['league'].isin(v_leagues)]
    if v_season: df_a = df_a[df_a['Season'].isin(v_season)]
    league_str_a = f" ({', '.join(v_leagues)})" if v_leagues and len(v_leagues) < len(league_options_all) else ""
    df_a['Label'] = f"A: {v_tournament.split(' (')[0]}{league_str_a}"
    
    df_b = df[df['player_name'].isin(players_b)].copy()
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
        monthly = compare_df.groupby(['Month_Num', 'Month', 'Label']).size().reset_index(name='Anzahl')
        
        # Determine X-Axis shift based on tournament A
        start_month_num = 7 # Default July
        if "EURO 2020" in v_tournament or "EURO 2024" in v_tournament:
            start_month_num = 6 # June
        elif "WM 2022" in v_tournament:
            start_month_num = 11 # November
            
        def get_display_order(m):
            return ((m - start_month_num) % 12) + 1
            
        monthly['Display_Order'] = monthly['Month_Num'].apply(get_display_order)
        monthly = monthly.sort_values(['Display_Order'])
        
        fig_month = px.line(
            monthly,
            x='Month',
            y='Anzahl',
            color='Label',
            color_discrete_map=color_map,
            markers=True,
            title="Verletzungen im Jahresverlauf (Vergleich)",
            labels={'Month': 'Monat', 'Anzahl': 'Anzahl Verletzungen', 'Label': 'Auswahl'}
        )
        
        # Add VRECT for Tournament Duration
        if "WM 2022" in v_tournament:
            fig_month.add_vrect(x0="November", x1="Dezember", fillcolor="yellow", opacity=0.3, line_width=0, annotation_text="WM 2022")
        elif "EURO 2020" in v_tournament:
            fig_month.add_vrect(x0="Juni", x1="Juli", fillcolor="blue", opacity=0.3, line_width=0, annotation_text="EURO 2020")
        elif "EURO 2024" in v_tournament:
            fig_month.add_vrect(x0="Juni", x1="Juli", fillcolor="green", opacity=0.3, line_width=0, annotation_text="EURO 2024")

        st.plotly_chart(fig_month, use_container_width=True)
    else:
        st.info("Keine Daten für diesen Vergleich verfügbar.")

    st.subheader("Verletzungsentwicklung über die Saisons")
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

# with tab_tables:
if False:
    st.markdown("""
    ### 📋 Für wen ist dieses Dashboard?
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
    ### ⚽ Für wen ist dieses Dashboard?
    **Zielgruppe:** Trainer, Athletik-Trainer, Positionscoaches, Scouts
    
    **Was sieht man?**
    - Interaktive Feldpositionen-Visualisierung (virtueller Fussballplatz)
    - Verletzungshäufigkeit nach Spielerposition
    - Positions-spezifische Verletzungsmuster
    - Betroffene Spieler pro Position
    - Strategische Insights für Aufstellung und Spielerrotation
    """)
    st.divider()
    
    st.subheader("Interaktive Karten")
    st.markdown("Analysiere die Verletzungen der Spieler nach Position in den einzelnen Clubs.")

    def create_soccer_map(data_df, global_min, global_max):
        if data_df.empty:
            return None

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

        club_df = data_df[data_df['player_position'].isin(position_coords.keys())].copy()

        if club_df.empty:
            return None

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
                "Injury": lambda x: ", ".join(sorted(set(map(str, x)))),
                "Days": "sum"
            })
            .reset_index()
        )

        injury_counts = injury_counts.merge(details, on="player_position", how="left")

        fig = go.Figure()

        fig.update_layout(
            height=450,
            plot_bgcolor="#6aa84f",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
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

        # Marker-Styling
        min_count = global_min
        max_count = global_max

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
                showscale=False,
                opacity=0.97
            ),
            customdata=injury_counts[['player_position', 'injury_count', 'player_name', 'Injury', 'Days']],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Anzahl Verletzungen: %{customdata[1]}<br>"
                "Ausfalltage insgesamt: %{customdata[4]:.0f}<br>"
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

        return fig

    # Compute global min and max for the color scale across all displayed data
    position_coords_keys = [
        "Goalkeeper", "Left-Back", "Centre-Back", "Right-Back", 
        "Defensive Midfield", "Central Midfield", "Attacking Midfield", 
        "Midfielder", "Left Midfield", "Right Midfield", 
        "Left Winger", "Right Winger", "Second Striker", "Forward"
    ]
    global_counts = filtered_df[filtered_df['player_position'].isin(position_coords_keys)].groupby(['league', 'player_position']).size().reset_index(name='count')
    if global_counts.empty:
        global_min, global_max = 0, 1
    else:
        global_min, global_max = global_counts['count'].min(), global_counts['count'].max()

    # Create a dummy horizontal colorbar
    if not global_counts.empty:
        fig_cbar = go.Figure(go.Scatter(
            x=[0], y=[0], mode="markers",
            marker=dict(
                size=0,
                color=[global_min, global_max],
                colorscale=[
                    [0.0, "#FEE2E2"],
                    [0.25, "#FCA5A5"],
                    [0.5, "#F87171"],
                    [0.75, "#DC2626"],
                    [1.0, "#7F1D1D"]
                ],
                cmin=global_min, cmax=global_max,
                showscale=True,
                colorbar=dict(
                    title="Anzahl Verletzungen",
                    orientation="h",
                    thickness=15,
                    yanchor="bottom", y=0,
                    xanchor="center", x=0.5,
                    len=0.6,
                    outlinewidth=0,
                )
            ),
            hoverinfo="none"
        ))
        fig_cbar.update_layout(
            height=100, 
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_cbar, use_container_width=True)

    if len(selected_leagues) == 1:
        # Single league - show one soccer map
        league = selected_leagues[0]
        title = f"Spielerpositionen mit Verletzungshäufung – {league}"
        if selected_club_global != "Alle Clubs":
            title += f" ({selected_club_global})"
        
        st.markdown(f"**{title}**")
        fig = create_soccer_map(filtered_df, global_min, global_max)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Keine Daten für die aktuelle Auswahl in der Kartenansicht verfügbar.")
    
    else:
        # Multiple leagues - show one soccer map per league, max 2 per row
        st.markdown("**Vergleich der Ligen:** Jede Karte zeigt die Verletzungsmuster nach Position einer Liga.")
        
        # Group leagues into pairs for display
        league_pairs = [selected_leagues[i:i+2] for i in range(0, len(selected_leagues), 2)]
        
        for pair in league_pairs:
            cols = st.columns(2)
            for idx, league in enumerate(pair):
                with cols[idx]:
                    league_df = filtered_df[filtered_df['league'] == league]
                    title = f"Spielerpositionen – {league}"
                    if selected_club_global != "Alle Clubs":
                        title += f" ({selected_club_global})"
                    
                    st.markdown(f"<div style='text-align: center;'><b>{title}</b></div>", unsafe_allow_html=True)
                    fig = create_soccer_map(league_df, global_min, global_max)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"Keine Daten für {league} verfügbar.")

with tab_bodymap:
    import pandas as pd
    import plotly.graph_objects as go

    st.markdown("""
    ### 🦵 Für wen ist dieses Dashboard?
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

    if filtered_df.empty:
        st.info("Keine Daten für die aktuelle Club-/Liga-/Saison-Auswahl in der Körperkarte verfügbar.")
    else:
        # -----------------------
        # Konfiguration
        # -----------------------
        position_coords = {
            "Head": (50, 124),
            "Neck": (50, 115),
            "Shoulder": (34.5, 108),
            "Chest/Ribs": (50, 106),
            "Back/Spine": (50, 96),
            "Abdomen/Core": (50, 82),
            "Hip/Groin": (50, 68),
            "Upper Arm": (31.5, 94),
            "Elbow": (31.5, 81.5),
            "Forearm": (31.5, 70),
            "Hand/Finger": (31.5, 60),
            "Thigh": (44.5, 56),
            "Knee": (44.5, 43.5),
            "Lower Leg": (44.5, 30),
            "Ankle": (50, 14),
            "Foot/Toe": (40.5, 15),
        }

        bodypart_display_mapping = {
            "Head": "Kopf",
            "Neck": "Nacken",
            "Shoulder": "Schulter",
            "Chest/Ribs": "Brust / Rippen",
            "Back/Spine": "Rücken / Wirbelsäule",
            "Abdomen/Core": "Bauch / Rumpf",
            "Hip/Groin": "Hüfte / Leiste",
            "Upper Arm": "Oberarm",
            "Elbow": "Ellbogen",
            "Forearm": "Unterarm",
            "Hand/Finger": "Hand / Finger",
            "Thigh": "Oberschenkel",
            "Knee": "Knie",
            "Lower Leg": "Unterschenkel",
            "Ankle": "Knöchel",
            "Foot/Toe": "Fuss / Zehen",
        }

        legend_category_mapping = {
            "Muskeln": "Muscle",
            "Knochen": "Bone",
            "Bänder": "Ligament",
            "Operation": "Surgery",
            "Krankheit": "Illness",
            "Leichte Verletzung": "Minor",
            "Nicht verletzungsbedingt": "Non-injury",
        }

        legend_items = [
            "Muskeln",
            "Knochen",
            "Bänder",
            "Operation",
            "Krankheit",
            "Leichte Verletzung",
            "Nicht verletzungsbedingt",
        ]

        category_colors = {
            "Muskeln": "#DC2626",
            "Knochen": "#7C3AED",
            "Bänder": "#2563EB",
            "Surgery": "#EA580C",
            "Illness": "#DB2777",
            "Minor": "#F59E0B",
            "Non-Injury": "#64748B",
        }

        body_categories = set(position_coords.keys())
        legend_categories = set(legend_category_mapping.values())

        colorscale = [
            [0.0, "#FEE2E2"],
            [0.25, "#FCA5A5"],
            [0.5, "#F87171"],
            [0.75, "#DC2626"],
            [1.0, "#7F1D1D"],
        ]

        def aggregate_injuries(df: pd.DataFrame) -> pd.DataFrame:
            if df.empty:
                return pd.DataFrame(columns=["injury_category", "injury_count", "player_name", "injury_type", "total_days"])

            return (
                df.groupby("injury_category", as_index=False)
                .agg(
                    injury_count=("injury_category", "size"),
                    player_name=("player_name", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))),
                    injury_type=("Injury", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))),
                    total_days=("Days", "sum")
                )
            )

        def get_text_color(value: int, vmin: int, vmax: int) -> str:
            if vmax == vmin:
                return "#FFFFFF"
            threshold = vmin + (vmax - vmin) * 0.55
            return "#FFFFFF" if value >= threshold else "#111827"

        def translate_bodypart(category: str) -> str:
            return bodypart_display_mapping.get(category, category)

        def format_hover_list_limited(value: str, items_per_line: int = 3, max_items: int = 8) -> str:
            if not value:
                return "Keine Angaben"

            items = [item.strip() for item in str(value).split(",") if item.strip()]
            if not items:
                return "Keine Angaben"

            shown_items = items[:max_items]
            lines = []

            for i in range(0, len(shown_items), items_per_line):
                lines.append(", ".join(shown_items[i:i + items_per_line]))

            result = "<br>".join(lines)

            if len(items) > max_items:
                result += f"<br><i>… und {len(items) - max_items} weitere</i>"

            return result

    def create_bodymap(data_df, global_min, global_max):
        body_df = data_df[data_df["injury_category"].isin(body_categories)].copy()
        body_counts = aggregate_injuries(body_df)

        if body_counts.empty:
            return None

        body_counts["x"] = body_counts["injury_category"].map(lambda cat: position_coords[cat][0])
        body_counts["y"] = body_counts["injury_category"].map(lambda cat: position_coords[cat][1])
        body_counts["display_category"] = body_counts["injury_category"].apply(translate_bodypart)
        body_counts["player_name_hover"] = body_counts["player_name"].apply(
            lambda x: format_hover_list_limited(x, items_per_line=3, max_items=8)
        )
        body_counts["injury_type_hover"] = body_counts["injury_type"].apply(
            lambda x: format_hover_list_limited(x, items_per_line=2, max_items=6)
        )

        legend_df = data_df[data_df["injury_category"].isin(legend_categories)].copy()
        legend_counts = aggregate_injuries(legend_df)

        legend_counts["display_category"] = legend_counts["injury_category"].apply(
            lambda x: next((k for k, v in legend_category_mapping.items() if v == x), x)
        )
        legend_counts["player_name_hover"] = legend_counts["player_name"].apply(
            lambda x: format_hover_list_limited(x, items_per_line=3, max_items=8)
        )
        legend_counts["injury_type_hover"] = legend_counts["injury_type"].apply(
            lambda x: format_hover_list_limited(x, items_per_line=2, max_items=6)
        )

        min_count = global_min
        max_count = global_max

        body_counts["text_color"] = body_counts["injury_count"].apply(
            lambda value: get_text_color(value, min_count, max_count)
        )

        fig = go.Figure()

        # Layout
        fig.update_layout(
            height=600,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=120, t=20, b=20),
            font=dict(
                family="Arial, sans-serif",
                color="#334155"
            ),
            hoverlabel=dict(
                bgcolor="#FFFFFF",
                bordercolor="#CBD5E1",
                font=dict(
                    color="#0F172A",
                    size=13,
                    family="Arial, sans-serif"
                ),
                align="left"
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

        body_line = dict(color="#94A3B8", width=1.8)
        body_fill = "#E9EEF5"
        joint_fill = "#F8FAFC"

        shapes = [
            dict(type="circle", x0=40, y0=114, x1=60, y1=134, line=body_line, fillcolor=joint_fill, layer="below"),
            dict(type="rect", x0=46, y0=109, x1=54, y1=114, line=dict(color="rgba(0,0,0,0)"), fillcolor=body_fill, layer="below"),
            dict(type="path", path="M 35 108 Q 34 92 35 72 L 65 72 Q 66 92 65 108 Q 58 114 50 114 Q 42 114 35 108 Z", line=body_line, fillcolor=body_fill, layer="below"),
            dict(type="path", path="M 35 108 Q 29 101 28 94 L 28 60 Q 28 57 31 57 L 35 57 L 35 106 Z", line=body_line, fillcolor="#F1F5F9", layer="below"),
            dict(type="path", path="M 65 108 Q 71 101 72 94 L 72 60 Q 72 57 69 57 L 65 57 L 65 106 Z", line=body_line, fillcolor="#F1F5F9", layer="below"),
            dict(type="circle", x0=28, y0=77, x1=35, y1=86, line=body_line, fillcolor=joint_fill, layer="below"),
            dict(type="circle", x0=65, y0=77, x1=72, y1=86, line=body_line, fillcolor=joint_fill, layer="below"),
            dict(type="path", path="M 40 72 L 60 72 L 58 64 L 42 64 Z", line=body_line, fillcolor="#D7DEE8", layer="below"),
            dict(type="path", path="M 42 64 L 49 64 L 49 20 L 40 20 L 40 58 Q 40 62 42 64 Z", line=body_line, fillcolor="#F1F5F9", layer="below"),
            dict(type="path", path="M 51 64 L 58 64 L 60 58 L 60 20 L 51 20 Z", line=body_line, fillcolor="#F1F5F9", layer="below"),
            dict(type="circle", x0=40, y0=39, x1=49, y1=48, line=body_line, fillcolor=joint_fill, layer="below"),
            dict(type="circle", x0=51, y0=39, x1=60, y1=48, line=body_line, fillcolor=joint_fill, layer="below"),
            dict(type="path", path="M 38 20 L 49 20 L 49 10 L 36 10 L 36 16 Q 36 20 38 20 Z", line=body_line, fillcolor="#E2E8F0", layer="below"),
            dict(type="path", path="M 51 20 L 62 20 Q 64 20 64 18 L 64 10 L 51 10 Z", line=body_line, fillcolor="#E2E8F0", layer="below"),
        ]
        fig.update_layout(shapes=shapes)

        # Seiten-Markierungen (L/R) neben dem Strichmännchen
        fig.add_annotation(x=25, y=50, text="<b>R</b>", showarrow=False, font=dict(size=32, color="#64748B"))
        fig.add_annotation(x=75, y=50, text="<b>L</b>", showarrow=False, font=dict(size=32, color="#64748B"))
        fig.add_annotation(x=25, y=43, text="Rechts", showarrow=False, font=dict(size=14, color="#94A3B8"))
        fig.add_annotation(x=75, y=43, text="Links", showarrow=False, font=dict(size=14, color="#94A3B8"))

        legend_x = 85
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

        visible_index = 0

        for label in legend_items:
            mapped_category = legend_category_mapping[label]
            row = legend_counts[legend_counts["injury_category"] == mapped_category]

            if row.empty:
                continue

            count = int(row.iloc[0]["injury_count"])
            if count <= 0:
                continue

            y = legend_y_start - visible_index * gap
            visible_index += 1

            player_name_hover = row.iloc[0]["player_name_hover"]
            injury_type_hover = row.iloc[0]["injury_type_hover"]
            text_color = get_text_color(count, min_count, max_count)

            total_days = int(row.iloc[0].get("total_days", 0))

            customdata = [[label, count, player_name_hover, injury_type_hover, total_days]]

            fig.add_trace(go.Scatter(
                x=[legend_x + 2],
                y=[y],
                mode="markers+text",
                text=[count],
                textposition="middle center",
                customdata=customdata,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Anzahl: %{customdata[1]}<br>"
                    "Ausfalltage: %{customdata[4]}<br><br>"
                    "<b>Spieler</b><br>%{customdata[2]}<br><br>"
                    "<b>Verletzungstypen</b><br>%{customdata[3]}"
                    "<extra></extra>"
                ),
                marker=dict(
                    size=22,
                    color=[count],
                    colorscale=colorscale,
                    cmin=min_count,
                    cmax=max_count,
                    line=dict(color="#FFFFFF", width=2.5),
                    opacity=0.97,
                    showscale=False
                ),
                textfont=dict(
                    size=12,
                    color="#000000",
                    family="Arial, sans-serif"
                ),
                showlegend=False
            ))

            fig.add_annotation(
                x=legend_x + 6,
                y=y,
                text=label,
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                font=dict(size=12, color="#475569")
            )

        hover_custom = body_counts[[
            "display_category",
            "injury_count",
            "player_name_hover",
            "injury_type_hover",
            "total_days"
        ]]

        fig.add_trace(go.Scatter(
            x=body_counts["x"],
            y=body_counts["y"],
            mode="markers+text",
            text=body_counts["injury_count"],
            textposition="middle center",
            customdata=hover_custom,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Anzahl: %{customdata[1]}<br>"
                "Ausfalltage insgesamt: %{customdata[4]:.0f}<br><br>"
                "<b>Spieler</b><br>%{customdata[2]}<br><br>"
                "<b>Verletzungstypen</b><br>%{customdata[3]}"
                "<extra></extra>"
            ),
            marker=dict(
                size=22,                    
                color=body_counts["injury_count"],
                colorscale=colorscale,
                cmin=min_count,
                cmax=max_count,
                line=dict(color="#FFFFFF", width=2.5),
                showscale=False,
                opacity=0.97
            ),
            textfont=dict(
                size=12,
                color="#000000",
                family="Arial, sans-serif"
            ),
            showlegend=False
        ))

        fig.add_annotation(
            x=50,
            y=2.5,
            text="Dunklere Marker zeigen häufiger registrierte Verletzungen",
            showarrow=False,
            font=dict(size=12, color="#64748B"),
            xanchor="center",
        )
        return fig

    if not filtered_df.empty:
        # Compute global min and max for the bodymaps
        league_body_df = filtered_df[filtered_df["injury_category"].isin(body_categories)].copy()
        if league_body_df.empty:
            global_min, global_max = 0, 1
        else:
            league_cat_counts = league_body_df.groupby(['league', 'injury_category']).size().reset_index(name='count')
            if league_cat_counts.empty:
                global_min, global_max = 0, 1
            else:
                global_min, global_max = league_cat_counts['count'].min(), league_cat_counts['count'].max()
    
        if not league_body_df.empty:
            fig_cbar = go.Figure(go.Scatter(
                x=[0], y=[0], mode="markers",
                marker=dict(
                    size=0,
                    color=[global_min, global_max],
                    colorscale=colorscale,
                    cmin=global_min, cmax=global_max,
                    showscale=True,
                    colorbar=dict(
                        title="Anzahl Verletzungen",
                        orientation="h",
                        thickness=15,
                        yanchor="bottom", y=0,
                        xanchor="center", x=0.5,
                        len=0.6,
                        outlinewidth=0,
                    )
                ),
                hoverinfo="none"
            ))
            fig_cbar.update_layout(
                height=100, 
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_cbar, use_container_width=True)
    
        if len(selected_leagues) == 1:
            league = selected_leagues[0]
            title = f"Verletzungshotspots nach Körperzone – {league}"
            if selected_club_global != "Alle Clubs":
                title += f" ({selected_club_global})"
            st.markdown(f"**{title}**")
            fig = create_bodymap(filtered_df, global_min, global_max)
            if fig:
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Keine Daten für die aktuelle Auswahl in der Körperkarte verfügbar.")
        else:
            st.markdown("**Vergleich der Ligen:** Jede Karte zeigt die Verletzungsmuster nach Körperzone einer Liga.")
            league_pairs = [selected_leagues[i:i+2] for i in range(0, len(selected_leagues), 2)]
            for pair in league_pairs:
                cols = st.columns(2)
                for idx, league in enumerate(pair):
                    with cols[idx]:
                        league_df = filtered_df[filtered_df['league'] == league]
                        title = f"Verletzungshotspots – {league}"
                        if selected_club_global != "Alle Clubs":
                            title += f" ({selected_club_global})"
                        st.markdown(f"<div style='text-align: center;'><b>{title}</b></div>", unsafe_allow_html=True)
                        fig = create_bodymap(league_df, global_min, global_max)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                        else:
                            st.info(f"Keine Daten für {league} verfügbar.")

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
    ### 💼 Für wen ist dieses Dashboard?
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
        - **Marktwert** = `market_value_in_eur` als finanzielle Basisgrösse.

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
        - Die höchsten Total_Days markieren die grössten produktiven und finanziellen Belastungstreiber.

        **Warum sinnvoll?**
        - Präventionsbudget fliesst zuerst in Verletzungstypen mit dem höchsten erwarteten ROI.

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
        - **Budget:** Prävention dort priorisieren, wo der grösste Risikoabbau pro investiertem Euro erwartet wird.
        - **Risikotragfähigkeit:** Gesamtrisikoquote des Kaders als Steuergrösse für Transfer- und Versicherungsstrategie nutzen.
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
    st.subheader("📈 DDDM: Verletzungsverlauf 2020–2025")
    st.markdown(
        "Diese Ansicht zeigt die Anzahl der Verletzungsfälle pro Saison. Wähle eine Verletzungsart, um den Verlauf gezielt zu analysieren."
    )

    trend_df = filtered_df.copy()

    if trend_df.empty:
        st.info("Keine Daten für den Verletzungsverlauf mit der aktuellen Filterauswahl.")
    else:
        injury_options = sorted(trend_df['Injury'].dropna().unique().tolist())
        selected_injury = st.selectbox(
            "Verletzungsart auswählen",
            ["Alle Verletzungen"] + injury_options,
            index=0
        )

        if selected_injury != "Alle Verletzungen":
            trend_df = trend_df[trend_df['Injury'] == selected_injury]

        counts = trend_df.groupby('Season').size().reset_index(name='Anzahl')

        if counts.empty:
            st.info("Für die gewählte Verletzungsart sind keine Daten vorhanden.")
        else:
            fig_trend = px.line(
                counts,
                x='Season',
                y='Anzahl',
                markers=True,
                title=(
                    "Verletzungsanzahl pro Saison"
                    if selected_injury == "Alle Verletzungen"
                    else f"Verlauf: {selected_injury.title()}"
                ),
                labels={'Season': 'Saison', 'Anzahl': 'Anzahl Verletzungen'}
            )
            fig_trend.update_layout(
                yaxis_title="Anzahl Verletzungen",
                xaxis_title="Saison",
                template="plotly_white",
                legend_title_text="Verletzungsart"
            )
            st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

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

with tab_market_risk:

    st.markdown("""
    ### 📉 Marktwert-Risiko & Verletzungskorrelation
    **Zielgruppe:** Sportliche Leitung, Scouts, Finanzabteilung
    
    **Was sieht man?**
    - Korrelation zwischen Marktwertentwicklung und Verletzungsphasen.
    - Finanzieller Impact: Wertverlust durch schwere Verletzungen.
    - Zeitliche Einordnung von Verletzungen in die Karriere-Wertkurve.
    """)
    st.divider()
    
    # --- Local Filters for Marktdaten ---
    with st.expander("🔍 Filter für Marktdaten & Suche", expanded=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            # Re-calculating player options based on current global filters
            player_options_local = sorted(df['player_name'].dropna().unique().tolist())
            st.session_state['player_search_val'] = st.multiselect(
                "Spieler suchen",
                options=player_options_local,
                default=[st.session_state['player_search']] if st.session_state['player_search'] else [],
                max_selections=1,
                help="Suche nach einem spezifischen Spieler."
            )
            st.session_state['player_search'] = st.session_state['player_search_val'][0] if st.session_state['player_search_val'] else ""
            player_search = st.session_state['player_search']

        with f_col2:
            st.session_state['tournament_filter'] = st.radio(
                "Turnier-Teilnahme Filter",
                options=TOURNAMENT_OPTIONS,
                index=TOURNAMENT_OPTIONS.index(st.session_state.get('tournament_filter', "Alle Spieler (Kein Filter)")) if st.session_state.get('tournament_filter') in TOURNAMENT_OPTIONS else 0,
                horizontal=True
            )
            tournament_filter = st.session_state['tournament_filter']
    
    st.divider()

    if player_search:
        # 1. Fetch player details for the "Steckbrief"
        p_name = player_search
        p_info = players_info_df[players_info_df['name'].str.contains(p_name, case=False, na=False)]
        
        if not p_info.empty:
            p_data = p_info.iloc[0]
            
            # --- Spieler-Steckbrief Layout ---
            st.markdown(f"## 👤 Spieler-Steckbrief: {p_data['name']}")
            
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
        p_injuries = filtered_df[filtered_df['player_name'].str.contains(p_name, case=False, na=False)].copy()
        p_valuations = val_df[val_df['name'].str.contains(p_name, case=False, na=False)].sort_values('date').copy()

        if not p_valuations.empty:
            st.subheader(f"Marktwert-Verlauf von {p_name}")

            # Filter for specific injuries to show in chart
            if not p_injuries.empty:
                # Prepare display labels for multiselect
                # Format: "Injury (X Wochen)"
                p_injuries['display_label'] = p_injuries.apply(
                    lambda row: f"{row['Injury']} ({int(row['Days'] // 7)} Wochen, ab {row['injury_from_parsed'].strftime('%d.%m.%y')})", 
                    axis=1
                )
                
                selected_vrects = st.multiselect(
                    "Einzublendende Verletzungen im Chart auswählen:",
                    options=p_injuries['display_label'].tolist(),
                    default=p_injuries['display_label'].tolist(),
                    help="Wähle aus, welche Verletzungsphasen als rote Flächen im Chart erscheinen sollen."
                )
                
                visible_injuries = p_injuries[p_injuries['display_label'].isin(selected_vrects)]
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
                    m5.metric("Veränderung (Delta)", f"{delta_pct:.1f}%", delta_color=delta_color)
                    
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
        else:
            st.warning(f"Keine Marktwert-Historie für '{p_name}' gefunden. Eventuell weicht der Name in der Transfermarkt-Datenbank leicht ab.")
    else:
        st.info("Wähle links in der Sidebar einen Spieler aus, um die detaillierte Marktwert-Risiko-Analyse zu sehen.")
        
        # Squad-Level Overview (Fallack)
        st.subheader("Globales Marktwert-Risiko (Top 10 Kader-Werte)")
        squad_mv = df.groupby('player_name')['market_value_in_eur'].first().sort_values(ascending=False).head(10).reset_index()
        fig_squad = px.bar(
            squad_mv,
            x='player_name',
            y='market_value_in_eur',
            title="Die 10 wertvollsten Spieler im aktiven Kader",
            labels={'player_name': 'Spieler', 'market_value_in_eur': 'Marktwert (EUR)'},
            color='market_value_in_eur',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_squad, use_container_width=True)

     