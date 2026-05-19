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
    
    # NEU: player_id als nullable Integer
    df['player_id'] = pd.to_numeric(df['player_id'], errors='coerce').astype('Int64')
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
        wm2022_games = df_games[(df_games['competition_id'] == 'FIWC') & (df_games['season'] == 2021)]['game_id'].unique()
        euro2024_games = df_games[(df_games['competition_id'] == 'EURO') & (df_games['season'] == 2023)]['game_id'].unique()

        euro2020_pids = set(df_events[df_events['game_id'].isin(euro2020_games)]['player_id'].dropna().unique())
        wm2022_pids = set(df_events[df_events['game_id'].isin(wm2022_games)]['player_id'].dropna().unique())
        euro2024_pids = set(df_events[df_events['game_id'].isin(euro2024_games)]['player_id'].dropna().unique())

        return euro2020_pids, wm2022_pids, euro2024_pids
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

@st.cache_data
def build_player_options(source_df, players_info_subset):
    """Erstellt eine Mapping-Tabelle: Anzeige-Label -> player_id"""
    unique_players = (source_df.dropna(subset=['player_id'])
                              .groupby('player_id')
                              .agg(name=('player_name', 'first'))
                              .reset_index())
    
    # Doppelte Namen erkennen und mit Geburtsjahr disambiguieren
    name_counts = unique_players['name'].value_counts()
    duplicate_names = name_counts[name_counts > 1].index
    
    # Geburtsjahr aus players_info_subset holen für Duplikate
    options = {}
    for _, row in unique_players.iterrows():
        p_id = int(row['player_id'])
        if row['name'] in duplicate_names:
            birth = players_info_subset.loc[players_info_subset['player_id'] == p_id, 'date_of_birth']
            year = pd.to_datetime(birth.iloc[0]).year if not birth.empty and pd.notna(birth.iloc[0]) else "?"
            label = f"{row['name']} (*{year})"
        else:
            label = row['name']
        options[label] = p_id
    
    return options

def calculate_contract_risk(player_data, market_value):
    """
    Berechnet Risiko-Metriken für Vertragsanalyse basierend auf durchschnittlichen Ausfalltagen
    
    Args:
        player_data: DataFrame mit Verletzungsdaten des Spielers
        market_value: Aktueller Marktwert in EUR
    
    Returns:
        dict mit Risiko-Metriken und Empfehlungen
    """
    if player_data.empty or pd.isna(market_value) or market_value == 0:
        return None
    
    total_days = player_data['Days'].sum()
    total_injuries = len(player_data)
    seasons_active = player_data['Season'].nunique()
    
    # Berechne durchschnittliche Ausfalltage pro Verletzung (Basis für Risikoklassifizierung)
    avg_days_per_injury = total_days / total_injuries if total_injuries > 0 else 0
    
    # Finanzielle Berechnungen
    career_years = 5
    daily_opportunity_cost = market_value / (career_years * 365)
    financial_impact = daily_opportunity_cost * total_days
    risk_percentage = (total_days / (career_years * 365)) * 100
    annual_impact = (total_days / max(seasons_active, 1)) * daily_opportunity_cost
    
    # Risiko-Level bestimmen basierend auf durchschnittlichen Ausfalltagen pro Verletzung
    if avg_days_per_injury > 60:
        risk_level = "🔴 Hohes Risiko"
        risk_color = "red"
        contract_action = f"""
        **Vertrag mit Vorsicht abschließen:**
        - Pay-per-Play oder leistungsbezogene Bonusstruktur erwägen
        - Kurze Bindungsfrist (max. 2 Jahre)
        - Versicherung/Absicherungsklauseln prüfen
        - Engere medizinische Betreuung kalkulieren
        - **Grund:** Ø {avg_days_per_injury:.1f} Tage pro Verletzung (hohe Schweregrad)
        """
    elif avg_days_per_injury > 30:
        risk_level = "🟡 Moderates Risiko"
        risk_color = "orange"
        contract_action = f"""
        **Standardvertrag mit Abstimmung:**
        - Normale Laufzeit (3-4 Jahre)
        - Leichte Performance-Bonuskomponente
        - Regelmäßige medizinische Checkups
        - **Grund:** Ø {avg_days_per_injury:.1f} Tage pro Verletzung (mittlere Schweregrad)
        """
    else:
        risk_level = "🟢 Geringes Risiko"
        risk_color = "green"
        contract_action = f"""
        **Unbedenkliche Vertragsverlängerung:**
        - Standard-Konditionen möglich
        - Stabilerer Asset-Value
        - Normale Belastungsplanung
        - **Grund:** Ø {avg_days_per_injury:.1f} Tage pro Verletzung (geringe Schweregrad)
        """
    
    return {
        "risk_level": risk_level,
        "risk_color": risk_color,
        "total_days": total_days,
        "total_injuries": total_injuries,
        "financial_impact": financial_impact,
        "risk_percentage": risk_percentage,
        "avg_days_per_injury": avg_days_per_injury,
        "annual_impact": annual_impact,
        "contract_action": contract_action
    }

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

    import random
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


def render_local_filters(tab_prefix):
    st.info("**Kurzanleitung:** Nutze den Turnierfilter, um gezielt die Verletzungen einer WM/EM-Kohorte (z. B. WM 2022) zu analysieren oder wähle 'Alle Spieler' für eine allgemeine Liga-Übersicht. Über den Saison-Filter kannst du den Zeitraum anpassen, um z. B. die Belastung während einer Turniersaison im Vergleich zu anderen Jahren zu untersuchen. Alle Grafiken passen sich automatisch deiner Auswahl an.", icon="💡")
    st.markdown("#### ⚙️ Filter (Turnier & Saison)")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            t_filter = st.selectbox("Turnierfilter", TOURNAMENT_OPTIONS, index=0, key=f"{tab_prefix}_tournament")
        with col2:
            s_filter = st.multiselect("Saisons", season_options, default=season_options, key=f"{tab_prefix}_seasons")
            
    local_df = df.copy()
    if s_filter:
        local_df = local_df[local_df['Season'].isin(s_filter)]
        
    if "Alle Spieler" not in t_filter:
        e20, w22, e24 = load_tournament_players()
        if "EURO 2020" in t_filter:
            local_df = local_df[local_df['player_id'].isin(e20)]
        elif "WM 2022" in t_filter:
            local_df = local_df[local_df['player_id'].isin(w22)]
        elif "EURO 2024" in t_filter:
            local_df = local_df[local_df['player_id'].isin(e24)]
        elif "WM und EM" in t_filter:
            local_df = local_df[local_df['player_id'].isin(e20.union(w22).union(e24))]
        elif "Keine Turnierteilnahme" in t_filter:
            all_t = e20.union(w22).union(e24)
            local_df = local_df[~local_df['player_id'].isin(all_t)]
            
    return local_df


# --- VISUALIZATION FUNCTIONS FOR DIALOGS ---

@st.dialog("Bodymap Details", width="large")
def open_bodymap_dialog(league, position, df):
    st.subheader(f"Verletzungen für: {position} ({league})")
    df_filtered = df[(df['league'] == league) & (df['player_position'] == position)]
    if df_filtered.empty:
        st.info("Keine Daten vorhanden.")
        return
        
    c1, c2 = st.columns([1, 1])
    with c1:
        # We need a body_df for create_bodymap. create_bodymap uses injury_category
        fig = create_bodymap(df_filtered, 0, len(df_filtered))
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.write("Verletzungs-Details")
        display_df = df_filtered[['player_name', 'club', 'Injury', 'Days']].copy()
        display_df.columns = ['Spieler', 'Verein', 'Verletzung', 'Ausfalltage']
        display_df = display_df.sort_values('Ausfalltage', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

@st.dialog("Spielfeld-Details", width="large")
def open_soccermap_dialog(league, body_part, df):
    # To translate the body part back to readable text if needed
    st.subheader(f"Positionen mit Verletzung in der {league}: {body_part}")
    
    # Check if the clicked part was from the legend
    # if body_part in legend_category_mapping values ... wait, body_categories vs legend
    # Let's filter df where injury_category == body_part
    df_filtered = df[(df['league'] == league) & (df['injury_category'] == body_part)]
    if df_filtered.empty:
        st.info("Keine Daten vorhanden.")
        return
        
    c1, c2 = st.columns([1, 1])
    with c1:
        fig = create_soccer_map(df_filtered, 0, len(df_filtered))
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.write("Verletzungs-Details")
        display_df = df_filtered[['player_name', 'club', 'Injury', 'Days', 'player_position']].copy()
        display_df.columns = ['Spieler', 'Verein', 'Verletzung', 'Ausfalltage', 'Position']
        display_df = display_df.sort_values('Ausfalltage', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)


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
    

    legend_x = 85
    legend_y_start = 112
    gap = 10
    
    fig.add_annotation(
        x=legend_x,
        y=legend_y_start + 10,
        text="<b>Kategorien</b>",
        showarrow=False,
        xanchor="left",
        font=dict(size=14, color="#475569")
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
    
        customdata = [[label, count, player_name_hover, injury_type_hover, total_days, mapped_category]]
    
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
                "Ausfalltage insgesamt: %{customdata[4]}"
                "<extra></extra>"
            ),
            marker=dict(
                size=30,
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
        "total_days",
        "injury_category"
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
            "Ausfalltage insgesamt: %{customdata[4]:.0f}"
            "<extra></extra>"
        ),
        marker=dict(
            size=30,                    
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
def create_soccer_map(data_df, global_min, global_max):
    if data_df.empty:
        return None

    position_coords = {
        "Goalkeeper": (5, 40),

        "Left-Back": (20, 65),
        "Centre-Back": (20, 40),
        "Right-Back": (20, 15),

        "Defensive Midfield": (37, 40),
        "Central Midfield": (55, 40),
        "Attacking Midfield": (73, 40),
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
        dict(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color="white", width=3), layer="below"),  # soccer field
        dict(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color="white", width=3), layer="below"),  # halfway line
        dict(type="circle", x0=50, y0=30, x1=70, y1=50, line=dict(color="white", width=3), layer="below"),  # center circle
        dict(type="circle", x0=59, y0=39, x1=61, y1=41, line=dict(color="white", width=2), fillcolor="white", layer="below"),  # center mark

        dict(type="rect", x0=0, y0=18, x1=18, y1=62, line=dict(color="white", width=3), layer="below"),  # goal area left
        dict(type="rect", x0=102, y0=18, x1=120, y1=62, line=dict(color="white", width=3), layer="below"),  # goal area right

        dict(type="rect", x0=0, y0=30, x1=6, y1=50, line=dict(color="white", width=3), layer="below"),  # penalty area left
        dict(type="rect", x0=114, y0=30, x1=120, y1=50, line=dict(color="white", width=3), layer="below"),  # penalty area right

        dict(type="circle", x0=10, y0=39, x1=12, y1=41, line=dict(color="white", width=2), fillcolor="white", layer="below"),  # penalty mark left
        dict(type="circle", x0=108, y0=39, x1=110, y1=41, line=dict(color="white", width=2), fillcolor="white", layer="below"),  # penalty mark right

        dict(type="path", path="M 18,32 Q 25,40 18,48", line_color="white", layer="below"),  # penalty arc left
        dict(type="path", path="M 102,32 Q 95,40 102,48", line_color="white", layer="below"),  # penalty arc right

        dict(type="path", path="M 0,76 Q 4,76 4,80", line_color="white", layer="below"),  # corner arc top left
        dict(type="path", path="M 0,4 Q 4,4 4,0", line_color="white", layer="below"),  # corner arc down left
        dict(type="path", path="M 120,76 Q 116,76 116,80", line_color="white", layer="below"),  # corner arc top right
        dict(type="path", path="M 120,4 Q 116,4 116,0", line_color="white", layer="below"),  # corner arc bottom right
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
            color="black",
            size=16,
            weight="bold"
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
            "Ausfalltage insgesamt: %{customdata[4]:.0f}<extra></extra>"
        )
    ))

    # Labels
    for _, row in injury_counts.iterrows():
        fig.add_annotation(
            x=row['x'],
            y=row['y'] - 6,
            text=row['player_position'],
            showarrow=False,
            font=dict(size=11, color="black")
        )

    fig.update_xaxes(visible=False, range=[0, 120])
    fig.update_yaxes(visible=False, range=[0, 80], scaleanchor="x", scaleratio=1)

    return fig

if "previous_selections" not in st.session_state:
    st.session_state.previous_selections = {}
dialog_already_opened = False
with tab_maps:
    st.header("⚽ Spielfeldanalyse")
    st.markdown("""
    **Welche Fragen werden dir in diesem Register beantwortet?**
    - In welchen Spielpositionen verletzen sich Spieler pro Liga am meisten?
    - Durch einen Klick auf eine beliebige Spielerposition: Welche Arten von Verletzungen ergeben sich pro Position?
                
    **Für wen?**
    - Trainer
    - Athletik-Trainer
    - Positionscoaches
    - Scouts
    
    **Was sieht man?**
    - Interaktive Feldpositionen-Visualisierung (virtueller Fussballplatz)
    - Verletzungshäufigkeit nach Spielerposition
    - Positions-spezifische Verletzungsmuster
    - Betroffene Spieler pro Position
    - Strategische Insights für Aufstellung und Spielerrotation
    - Vergleich der Verletzungsmuster während den Grossturnieren (z. B. WM/EM) und regulären Saisons
    """)
    st.divider()
    
    st.subheader("🥅 Interaktives Spielfeld")
    st.markdown("Analysiere die Verletzungen der Spieler nach Position in den einzelnen Clubs.")
    st.info("""
    💡 **Kurzanleitung zur interaktiven Karte:**
    - **Details anzeigen:** Klicke auf eine beliebige Position (z. B. Centre-Back) auf dem Spielfeld. Es öffnet sich ein neues Fenster mit einer Körperkarte und Tabelle, die dir genau zeigt, welche Körperteile bei der ausgewählten Position am häufigsten verletzt wurden.
    - **Fenster schliessen:** Klicke einfach auf das 'X' oben rechts oder neben das Fenster, um zur Spielfeld-Übersicht zurückzukehren.
    - **Auswahl aufheben:** Wenn du eine Position angeklickt hast, bleibt sie markiert. Mache einfach einen **Doppelklick** auf den leeren grünen Rasen, um die Auswahl aufzuheben und die Karte zurückzusetzen.
    """)
    
    maps_df = render_local_filters("maps")


    # Compute global min and max for the color scale across all displayed data
    position_coords_keys = [
        "Goalkeeper", "Left-Back", "Centre-Back", "Right-Back", 
        "Defensive Midfield", "Central Midfield", "Attacking Midfield", 
        "Midfielder", "Left Midfield", "Right Midfield", 
        "Left Winger", "Right Winger", "Second Striker", "Forward"
    ]
    global_counts = maps_df[maps_df['player_position'].isin(position_coords_keys)].groupby(['league', 'player_position']).size().reset_index(name='count')
    if global_counts.empty:
        global_min, global_max = 0, 1
    else:
        global_min, global_max = global_counts['count'].min(), global_counts['count'].max()

    # Create a dummy horizontal colorbar
    if not global_counts.empty:
        fig_cbar = go.Figure(go.Scatter(
            x=[-10], y=[-10], mode="markers",
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
            xaxis=dict(visible=False, range=[0, 1]), yaxis=dict(visible=False, range=[0, 1]),
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
        fig = create_soccer_map(maps_df, global_min, global_max)
        if fig:
            event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key=f"soccer_map_single_{league}")
            current_sel = event.selection["points"][0]["customdata"][0] if event and event.selection.get("points") else None
            prev_sel = st.session_state.previous_selections.get(f"soccer_map_single_{league}")
            if current_sel and current_sel != prev_sel and not dialog_already_opened:
                dialog_already_opened = True
                st.session_state.previous_selections[f"soccer_map_single_{league}"] = current_sel
                open_bodymap_dialog(league, current_sel, maps_df)
            elif not current_sel:
                st.session_state.previous_selections[f"soccer_map_single_{league}"] = None
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
                    league_df = maps_df[maps_df['league'] == league]
                    title = f"Spielerpositionen – {league}"
                    if selected_club_global != "Alle Clubs":
                        title += f" ({selected_club_global})"
                    
                    st.markdown(f"<div style='text-align: center;'><b>{title}</b></div>", unsafe_allow_html=True)
                    fig = create_soccer_map(league_df, global_min, global_max)
                    if fig:
                        event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key=f"soccer_map_multi_{league}")
                        current_sel = event.selection["points"][0]["customdata"][0] if event and event.selection.get("points") else None
                        prev_sel = st.session_state.previous_selections.get(f"soccer_map_multi_{league}")
                        if current_sel and current_sel != prev_sel and not dialog_already_opened:
                            dialog_already_opened = True
                            st.session_state.previous_selections[f"soccer_map_multi_{league}"] = current_sel
                            open_bodymap_dialog(league, current_sel, maps_df)
                        elif not current_sel:
                            st.session_state.previous_selections[f"soccer_map_multi_{league}"] = None
                    else:
                        st.info(f"Keine Daten für {league} verfügbar.")

with tab_bodymap:
    import pandas as pd
    import plotly.graph_objects as go

    st.header("🦵 Körperregionanalyse")
    st.markdown("""
    **Welche Fragen werden dir in diesem Register beantwortet?**                
    - Welche Körperregionen sind am häufigsten von Verletzungen betroffen?
    - Welche anatomischen Schwachstellen zeigen sich je nach Liga oder Saison?
    - Welche Verletzungsarten zeigen die einzelnen Top-Ligen im Vergleich?
    - Durch einen Klick auf eine beliebige Körperregion: Welche Spielerpositionen sind am häufigsten von Verletzungen dieser Körperregion betroffen?
             
    **Für wen?**
    - Medizinisches Personal
    - Physiotherapeuten
    - Sportmediziner
    - Forscher

    **Was sieht man?**
    - Verletzungen nach Körperregion (Muskeln, Knie, Knöchel, etc.)
    - Anatomische Schwachpunkte pro Liga für gezielte Präventions- und Rehabilitationsmassnahmen
    - Häufigste Verletzungstypen nach Körperteil
    - Vergleich der Verletzungsmuster während den Grossturnieren (z. B. WM/EM) und regulären Saisons
    """)
    st.divider()

    st.subheader("🧍‍♂️ Interaktive Körperkarte")
    st.markdown("Analysiere die Verletzungen der Spieler anhand der Körperregionen.")
    st.info("""
    💡 **Kurzanleitung zur interaktiven Körperkarte:**
    - **Details anzeigen:** Klicke auf ein beliebiges Körperteil (z. B. Knie) am Körper oder auf einen Punkt in der Legende. Es öffnet sich ein neues Fenster mit einem Spielfeld und einer Tabelle, die dir exakt zeigt, auf welchen Spielerpositionen diese Verletzung am häufigsten auftritt.
    - **Fenster schliessen:** Klicke einfach auf das 'X' oben rechts oder neben das Fenster, um zur Bodymap-Übersicht zurückzukehren.
    - **Auswahl aufheben:** Wenn du ein Körperteil angeklickt hast, bleibt es markiert. Mache einfach einen **Doppelklick** auf einen leeren Bereich neben dem Strichmännchen, um die Auswahl aufzuheben und die Karte zurückzusetzen.
    """)

    body_df = render_local_filters("bodymap")

    if body_df.empty:
        st.info("Keine Daten für die aktuelle Saison-Auswahl in der Körperkarte verfügbar.")

    if not body_df.empty:
        league_body_df = body_df[body_df["injury_category"].isin(body_categories)].copy()
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
                x=[-10], y=[-10], mode="markers",
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
                xaxis=dict(visible=False, range=[0, 1]), yaxis=dict(visible=False, range=[0, 1]),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_cbar, use_container_width=True, key="bodymap_colorbar")
    
        if len(selected_leagues) == 1:
            league = selected_leagues[0]
            title = f"Verletzungshotspots nach Körperzone – {league}"
            if selected_club_global != "Alle Clubs":
                title += f" ({selected_club_global})"
            st.markdown(f"**{title}**")
            fig = create_bodymap(body_df, global_min, global_max)
            if fig:
                event = st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, on_select="rerun", key=f"bodymap_single_{league}")
                current_sel = event.selection["points"][0]["customdata"][5] if event and event.selection.get("points") else None
                prev_sel = st.session_state.previous_selections.get(f"bodymap_single_{league}")
                if current_sel and current_sel != prev_sel and not dialog_already_opened:
                    dialog_already_opened = True
                    st.session_state.previous_selections[f"bodymap_single_{league}"] = current_sel
                    open_soccermap_dialog(league, current_sel, body_df)
                elif not current_sel:
                    st.session_state.previous_selections[f"bodymap_single_{league}"] = None
            else:
                st.info("Keine Daten für die aktuelle Auswahl in der Körperkarte verfügbar.")
        else:
            st.markdown("**Vergleich der Ligen:** Jede Karte zeigt die Verletzungsmuster nach Körperzone einer Liga.")
            league_pairs = [selected_leagues[i:i+2] for i in range(0, len(selected_leagues), 2)]
            for pair in league_pairs:
                cols = st.columns(2)
                for idx, league in enumerate(pair):
                    with cols[idx]:
                        league_df = body_df[body_df['league'] == league]
                        title = f"Verletzungshotspots – {league}"
                        if selected_club_global != "Alle Clubs":
                            title += f" ({selected_club_global})"
                        st.markdown(f"<div style='text-align: center;'><b>{title}</b></div>", unsafe_allow_html=True)
                        fig = create_bodymap(league_df, global_min, global_max)
                        if fig:
                            event = st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, on_select="rerun", key=f"bodymap_multi_{league}")
                            current_sel = event.selection["points"][0]["customdata"][5] if event and event.selection.get("points") else None
                            prev_sel = st.session_state.previous_selections.get(f"bodymap_multi_{league}")
                            if current_sel and current_sel != prev_sel and not dialog_already_opened:
                                dialog_already_opened = True
                                st.session_state.previous_selections[f"bodymap_multi_{league}"] = current_sel
                                open_soccermap_dialog(league, current_sel, body_df)
                            elif not current_sel:
                                st.session_state.previous_selections[f"bodymap_multi_{league}"] = None
                        else:
                            st.info(f"Keine Daten für {league} verfügbar.")

with tab_dddm:
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




with tab_market_risk:

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
                m_col3.metric("Ø Marktwert-Trend", f"{avg_impact:+.1f}%", delta=f"{avg_impact:.1f}%", delta_color="normal" if avg_impact >= 0 else "inverse")
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

with tab_simulator:
    st.header("🔮 Verletzungs-Simulator: Marktwert-Auswirkung")
    st.markdown("""
    **Welche Fragen werden dir in diesem Register beantwortet?**                
    - Wie stark würde sich eine hypothetische Verletzung auf den Marktwert eines Spielers auswirken?
    - Welche Verletzungsarten verursachen den grössten finanziellen Schaden?
    - Wie verändert sich der Marktwert je nach Ausfallzeit?
                    
    **Für wen?**
    - Sportdirektor
    - Scouts
    - CFO / Club-Manager
                
    **Was sieht man?**
    - **Machine Learning-Prognose:** Vorhersage des Marktwertverlusta bei einer hypothetischen Verletzung
    - **Spielerspezifische Simulation:** Basierend auf Spielerdaten (Alter, Position, Liga, Historie)
    - **Generischer Simulator:** Manuelle Parametereingabe für theoretische Szenarien
    - **SHAP-Explainability:** Verständnis, welche Faktoren die Vorhersage treiben
    - **Vertragsverhandlung:** Finanzielle Risikobewertung für Vertragsverhandlungen
    """)
    st.divider()

    import sys
    import os
    import matplotlib.pyplot as plt
    import shap
        
    try:
        from machine_learning.ml_predict import predict_market_change
        
        # --- Gemeinsame Ergebnis-Anzeige Funktion ---
        def display_prediction_results(res, player_label=None):
            """Zeigt die Vorhersage-Ergebnisse, Handlungsempfehlung und SHAP-Plot an."""
            st.divider()
            if player_label:
                st.subheader(f"📊 Prognoseergebnis für {player_label}")
            else:
                st.subheader("📊 Prognoseergebnis")
            
            k_col1, k_col2, k_col3 = st.columns(3)
            drop_pct = res['drop_pct']
            
            k_col1.metric("Erwartete Marktwertänderung", f"{drop_pct:.1f} %", delta=f"{drop_pct:.1f}%", delta_color="inverse")
            k_col2.metric("Finanzieller Verlust (EUR)", f"€ {res['loss_eur']/1e6:.2f} Mio.", delta=f"€ {res['loss_eur']/1e6:.2f}M", delta_color="inverse")
            k_col3.metric("Neuer Marktwert", f"€ {res['new_mv']/1e6:.2f} Mio.")
            
            st.markdown("### 💡 Handlungsempfehlung")
            if drop_pct > -5.0:
                st.success("🟢 **Geringes Risiko:** Der zu erwartende Marktwertverlust ist minimal. Keine akuten vertraglichen Massnahmen zwingend erforderlich.")
            elif drop_pct > -15.0:
                st.warning("🟡 **Mittleres Risiko:** Spürbarer Einfluss auf den Marktwert. Bei Vertragsverhandlungen sollte die Verletzungshistorie berücksichtigt werden.")
            else:
                st.error("🔴 **Hohes Risiko:** Signifikanter Marktwertverlust! Es wird empfohlen, Leistungsklauseln in zukünftige Verträge aufzunehmen und einen Notfallplan für diese Position zu prüfen.")
                
            st.markdown("### 🧠 Erklärbarkeit der Vorhersage (SHAP)")
            
            tab_local, tab_global = st.tabs(["Lokal (Waterfall Plot)", "Global (Beeswarm Plot)"])
            
            with tab_local:
                st.write("**Individuelle Vorhersage:** Dieser Plot zeigt, wie jedes einzelne Merkmal (blau = Wertsteigernd/weniger Verlust, rot = Wertmindernd/mehr Verlust) die **aktuelle** Vorhersage des XGBoost-Modells gebildet hat.")
                fig, ax = plt.subplots(figsize=(10, 6))
                shap.plots.waterfall(res['shap_values'][0], show=False)
                st.pyplot(fig, clear_figure=True)
                
            with tab_global:
                st.write("**Allgemeines Modellverhalten:** Dieser Plot zeigt die globale Wichtigkeit und den Einfluss der Features über eine grosse Stichprobe des Modells hinweg. Jeder Punkt ist eine historische Verletzung. Rote Punkte stehen für hohe Feature-Werte (z.B. hohes Alter), blaue für niedrige.")
                
                from machine_learning.ml_predict import get_global_shap_data
                global_shap_values = get_global_shap_data()
                
                if global_shap_values is not None:
                    fig2, ax2 = plt.subplots(figsize=(10, 6))
                    shap.plots.beeswarm(global_shap_values, show=False)
                    st.pyplot(fig2, clear_figure=True)
                else:
                    st.info("Globale SHAP-Werte wurden nicht im Modell gespeichert. Bitte das Modell mit dem aktualisierten Skript neu trainieren.")
        
        # --- Zwei Sub-Tabs ---
        sim_tab_player, sim_tab_generic = st.tabs(["🔍 Spieler-Suche", "⚙️ Generischer Simulator"])
        
        # ===========================
        # SUB-TAB 1: SPIELER-SUCHE
        # ===========================
        with sim_tab_player:
            st.markdown("""
            > Suche einen konkreten Spieler aus dem Datensatz. Seine Daten werden automatisch übernommen. 
            > Du wählst nur noch die **hypothetische Verletzung** aus.
            """)
            def on_player_select():
                """Callback: Aktualisiert Session State nur wenn Widget sich ändert"""
                selection = st.session_state.player_search_widget
                st.session_state['risk_selected_player'] = selection[0] if selection else None
            # Spieler-Suche – gleicher Stil wie im Marktwert-Tab (Multiselect)
            player_options_local_sim = sorted(player_options_map.keys())
            sel_sim_p = st.multiselect(
                "👤 Spieler suchen",
                options=player_options_local_sim,
                default=[],
                max_selections=1,
                help="Wähle einen Spieler aus, um seinen Steckbrief und eine Verletzungs-Simulation zu sehen.",
                key="sim_player_multiselect",
                on_change=on_player_select
                )   

            
            sim_selected_player_id = player_options_map.get(sel_sim_p[0]) if sel_sim_p else None
            
            if sim_selected_player_id is not None:
                # Spieler-Daten aus dem Datensatz laden
                player_injuries = df[df['player_id'] == sim_selected_player_id].sort_values('injury_from_parsed')
                player_info = players_info_df[players_info_df['player_id'] == sim_selected_player_id]
                
                if not player_injuries.empty:
                    # Spieler-Profil anzeigen
                    p_name = player_injuries['player_name'].iloc[0]
                    p_age = int(player_injuries['player_age'].iloc[-1]) if pd.notna(player_injuries['player_age'].iloc[-1]) else 25
                    p_position = player_injuries['player_position'].iloc[0] if pd.notna(player_injuries['player_position'].iloc[0]) else "Unknown"
                    p_league = player_injuries['league'].iloc[-1] if pd.notna(player_injuries['league'].iloc[-1]) else "Unknown"
                    p_club = player_injuries['club'].iloc[-1] if pd.notna(player_injuries['club'].iloc[-1]) else "Unbekannt"
                    
                    # Marktwert: neuester aus val_df oder aus dem Injury-Datensatz
                    p_val_data = val_df[val_df['player_id'] == sim_selected_player_id].sort_values('date')
                    if not p_val_data.empty and pd.notna(p_val_data.iloc[-1]['market_value_in_eur']):
                        p_mv = int(p_val_data.iloc[-1]['market_value_in_eur'])
                    elif not player_info.empty and 'market_value_in_eur' in player_info.columns and pd.notna(player_info.iloc[0]['market_value_in_eur']):
                        p_mv = int(player_info.iloc[0]['market_value_in_eur'])
                    else:
                        p_mv = 1000000  # Fallback
                    
                    # Verletzungshistorie berechnen
                    p_prev_injuries = len(player_injuries)
                    p_prev_days = int(player_injuries['Days'].fillna(0).sum())
                    
                    # --- Spieler-Steckbrief (identisch zum Marktwert-Tab) ---
                    st.markdown(f"### 👤 Spieler-Steckbrief: {p_name}")
                    
                    if not player_info.empty:
                        p_data = player_info.iloc[0]
                        
                        prof_col1, prof_col2 = st.columns([0.8, 3.2])
                        
                        with prof_col1:
                            # Spieler-Bild von Transfermarkt
                            if pd.notna(p_data.get('image_url', None)):
                                st.image(p_data['image_url'], use_container_width=True)
                            else:
                                st.info("Kein Bild verfügbar")
                        
                        with prof_col2:
                            stat_col1, stat_col2 = st.columns(2)
                            
                            with stat_col1:
                                st.write(f"**Nationalität:** {p_data['country_of_citizenship']}" if pd.notna(p_data.get('country_of_citizenship')) else "**Nationalität:** Unbekannt")
                                st.write(f"**Geburtsdatum:** {pd.to_datetime(p_data['date_of_birth']).strftime('%d.%m.%Y')}" if pd.notna(p_data.get('date_of_birth')) else "**Geburtsdatum:** Unbekannt")
                                st.write(f"**Position:** {p_data['position']}" if pd.notna(p_data.get('position')) else f"**Position:** {p_position}")
                                st.write(f"**Starker Fuss:** {p_data['foot'].capitalize()}" if pd.notna(p_data.get('foot')) else "**Starker Fuss:** Unbekannt")
                                
                                # Club Logo
                                c_name = p_data.get('current_club_name', p_club)
                                c_id = p_data.get('current_club_id', None)
                                if pd.notna(c_id):
                                    logo_url = f"https://tmssl.akamaized.net/images/wappen/medium/{int(c_id)}.png"
                                    st.markdown(f"**Aktueller Club:** {c_name}")
                                    st.image(logo_url, width=60)
                                else:
                                    st.write(f"**Aktueller Club:** {c_name}")
                            
                            with stat_col2:
                                st.write(f"**Grösse:** {int(p_data['height_in_cm'])} cm" if pd.notna(p_data.get('height_in_cm')) else "**Grösse:** Unbekannt")
                                st.write(f"**Länderspiele:** {int(p_data['international_caps'])}" if pd.notna(p_data.get('international_caps')) else "**Länderspiele:** 0")
                                st.write(f"**Länderspieltore:** {int(p_data['international_goals'])}" if pd.notna(p_data.get('international_goals')) else "**Länderspieltore:** 0")
                                st.write(f"**Bisherige Verletzungen:** {p_prev_injuries}")
                                st.write(f"**Kumulierte Ausfalltage:** {p_prev_days}")
                            
                            st.divider()
                            m1, m2 = st.columns(2)
                            m1.metric("Aktueller Marktwert", f"€{p_mv:,.0f}".replace(",", "."))
                            if pd.notna(p_data.get('highest_market_value_in_eur')):
                                m2.metric("Höchster Marktwert", f"€{p_data['highest_market_value_in_eur']:,.0f}".replace(",", "."))
                    else:
                        # Fallback: Einfache Karte, wenn keine players_info vorhanden
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                                    padding: 20px; border-radius: 12px; margin-bottom: 20px; color: white;">
                            <h3 style="margin: 0 0 12px 0; color: #f8fafc;">⚽ {p_name}</h3>
                            <p>Position: {p_position} | Liga: {p_league} | Alter: {p_age} | Marktwert: €{p_mv:,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # Nur noch Verletzung und Ausfalltage eingeben
                    st.markdown("#### 🔮 Was-wäre-wenn: Verletzungsszenario simulieren")
                    sim_p_col1, sim_p_col2 = st.columns(2)
                    with sim_p_col1:
                        sim_p_category = st.selectbox("Verletzungskategorie", df['injury_category'].dropna().unique().tolist(), key="sim_p_cat")
                    with sim_p_col2:
                        sim_p_days = st.slider("Erwartete Ausfalltage", 1, 400, 30, key="sim_p_days")
                    
                    if st.button("🔮 Vorhersage für diesen Spieler berechnen", use_container_width=True, type="primary", key="sim_p_btn"):
                        with st.spinner(f"Berechne Prognose für {p_name}..."):
                            res = predict_market_change(
                                age=p_age,
                                position=p_position,
                                injury_category=sim_p_category,
                                days_out=sim_p_days,
                                current_mv=float(p_mv),
                                league=p_league,
                                prev_injuries=p_prev_injuries,
                                total_prev_days=p_prev_days
                            )
                        display_prediction_results(res, player_label=p_name)
                else:
                    st.warning("Keine Verletzungsdaten für diesen Spieler gefunden.")
        
        # ===========================
        # SUB-TAB 2: GENERISCHER SIMULATOR
        # ===========================
        with sim_tab_generic:
            st.markdown("""
            > Stelle die Parameter manuell ein, um ein hypothetisches Spielerprofil zu simulieren.
            > Ideal für allgemeine Risikobewertungen oder Transfer-Due-Diligence.
            """)
            
            col_in1, col_in2, col_in3 = st.columns(3)
            with col_in1:
                sim_age = st.slider("Alter", 16, 40, 25, key="gen_age")
                sim_position = st.selectbox("Position", df['player_position'].dropna().unique().tolist(), key="gen_pos")
                sim_league = st.selectbox("Liga", df['league'].dropna().unique().tolist(), key="gen_league")
            with col_in2:
                sim_category = st.selectbox("Verletzungskategorie", df['injury_category'].dropna().unique().tolist(), key="gen_cat")
                sim_days = st.slider("Erwartete Ausfalltage", 1, 400, 30, key="gen_days")
                sim_mv = st.number_input("Aktueller Marktwert (€)", min_value=100000, max_value=250000000, value=25000000, step=1000000, key="gen_mv")
            with col_in3:
                sim_prev_inj = st.slider("Anzahl vorheriger Verletzungen", 0, 10, 0, key="gen_prev_inj")
                sim_prev_days = st.slider("Kumulierte Ausfalltage bisher", 0, 1000, 0, key="gen_prev_days")
                
            if st.button("🔮 Vorhersage berechnen", use_container_width=True, type="primary", key="gen_btn"):
                with st.spinner("Berechne Machine-Learning-Prognose..."):
                    res = predict_market_change(
                        age=sim_age,
                        position=sim_position,
                        injury_category=sim_category,
                        days_out=sim_days,
                        current_mv=sim_mv,
                        league=sim_league,
                        prev_injuries=sim_prev_inj,
                        total_prev_days=sim_prev_days
                    )
                display_prediction_results(res)
            
    except Exception as e:
        st.error(f"Fehler beim Laden des ML-Modells. Bitte stelle sicher, dass 'machine_learning/train_model.py' erfolgreich ausgeführt wurde. Details: {e}")