import pandas as pd
import os
import streamlit as st

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

@st.cache_data
def load_clubs():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    clubs_path = os.path.join(script_dir, "../Data/clubs.csv")
    clubs_df = pd.read_csv(clubs_path)
    return clubs_df
