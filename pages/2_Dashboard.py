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
from utils.data_loader import load_data, load_valuation_data, load_players_full, load_tournament_players, load_clubs
from utils.helpers import get_injury_color, build_player_options, calculate_contract_risk

df = load_data()
val_df = load_valuation_data()
players_info_df = load_players_full()
clubs_info_df = load_clubs()

player_options_map = build_player_options(df, players_info_df[['player_id', 'date_of_birth']])


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
    st.session_state['filter_seasons'] = season_options
if 'filter_players' not in st.session_state:
    st.session_state['filter_players'] = []
if 'risk_display_count' not in st.session_state:
    st.session_state['risk_display_count'] = 50
if 'risk_selected_player' not in st.session_state:
    st.session_state['risk_selected_player'] = None
if 'dddm_selected_player' not in st.session_state:
    st.session_state['dddm_selected_player'] = None
if 'dddm_filter_club' not in st.session_state:
    st.session_state['dddm_filter_club'] = "Alle Clubs"
if 'dddm_filter_seasons' not in st.session_state:
    st.session_state['dddm_filter_seasons'] = season_options
if 'dddm_filter_leagues' not in st.session_state:
    st.session_state['dddm_filter_leagues'] = sorted(df['league'].dropna().unique().tolist())

# --- Global Filter UI ---

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


min_date = df['injury_from_parsed'].min().date()
max_date = df['injury_from_parsed'].max().date()


if 'date_range' not in st.session_state:
    st.session_state['date_range'] = (min_date, max_date)
date_range = st.session_state['date_range']



if 'tournament_filter' not in st.session_state:
    st.session_state['tournament_filter'] = "Alle Spieler (Kein Filter)"
tournament_filter = st.session_state['tournament_filter']



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
        player_source_df = player_source_df[player_source_df['player_id'].isin(e20)]
    elif "WM 2022" in tournament_filter:
        player_source_df = player_source_df[player_source_df['player_id'].isin(w22)]
    elif "EURO 2024" in tournament_filter:
        player_source_df = player_source_df[player_source_df['player_id'].isin(e24)]
    elif "WM und EM" in tournament_filter:
        player_source_df = player_source_df[player_source_df['player_id'].isin(e20.union(w22).union(e24))]
    elif "Keine Turnierteilnahme" in tournament_filter:
        all_tournament_players = e20.union(w22).union(e24)
        player_source_df = player_source_df[~player_source_df['player_id'].isin(all_tournament_players)]

player_options = sorted(player_source_df['player_name'].dropna().unique().tolist())
st.session_state['filter_players'] = [p for p in st.session_state['filter_players'] if p in player_options]


if 'player_search' not in st.session_state:
    st.session_state['player_search'] = ""
player_search = st.session_state['player_search']



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
        filtered_df = filtered_df[filtered_df['player_id'].isin(e20)]
    elif "WM 2022" in tournament_filter:
        filtered_df = filtered_df[filtered_df['player_id'].isin(w22)]
    elif "EURO 2024" in tournament_filter:
        filtered_df = filtered_df[filtered_df['player_id'].isin(e24)]
    elif "WM und EM" in tournament_filter:
        filtered_df = filtered_df[filtered_df['player_id'].isin(e20.union(w22).union(e24))]
    elif "Keine Turnierteilnahme" in tournament_filter:
        all_tournament_players = e20.union(w22).union(e24)
        filtered_df = filtered_df[~filtered_df['player_id'].isin(all_tournament_players)]

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
    "Zeitvergleich & Trends",
    "Spielfeldanalyse",    
    "Körperregionanalyse",
    "Clubanalyse",
    "Marktwert- & Risikoanalyse",
    "Verletzungssimulator"
]

# Ensure active_tab is in session state and handle redirection
if "tab" in st.query_params:
    st.session_state["active_dashboard_tab"] = st.query_params["tab"]
elif "requested_tab" in st.session_state:
    st.session_state["active_dashboard_tab"] = st.session_state["requested_tab"]
    del st.session_state["requested_tab"]

if "active_dashboard_tab" not in st.session_state:
    st.session_state["active_dashboard_tab"] = "Zeitvergleich & Trends"

def update_tab_url():
    """Updates the URL query parameters when a tab is clicked."""
    st.query_params["tab"] = st.session_state["active_dashboard_tab"]

tab_trends, tab_maps, tab_bodymap, tab_dddm, tab_market_risk, tab_simulator = st.tabs(
    tab_labels, 
    key="active_dashboard_tab",
    on_change=update_tab_url
)



with tab_trends:
    from pages.dashboard_tabs import trends
    trends.render(df, filtered_df, players_info_df, selected_leagues, TOURNAMENT_OPTIONS, season_options)


from utils.visualizations import render_local_filters, open_bodymap_dialog, open_soccermap_dialog, create_bodymap, create_soccer_map, body_categories, colorscale
if "previous_selections" not in st.session_state:
    st.session_state.previous_selections = {}
dialog_already_opened = False
with tab_maps:
    from pages.dashboard_tabs import soccermap
    soccermap.render(df, selected_leagues, selected_club_global, TOURNAMENT_OPTIONS, season_options)

with tab_bodymap:
    from pages.dashboard_tabs import bodymap
    bodymap.render(df, selected_leagues, selected_club_global, TOURNAMENT_OPTIONS, season_options)

with tab_dddm:
    from pages.dashboard_tabs import clubanalyse
    clubanalyse.render(df, filtered_df, selected_seasons, DEFAULT_SEASON, club_options, season_options)

with tab_market_risk:
    from pages.dashboard_tabs import market_risk
    market_risk.render(df, filtered_df, val_df, players_info_df, player_options_map)

with tab_simulator:
    from pages.dashboard_tabs import simulator
    simulator.render(df, val_df, players_info_df, player_options_map)

