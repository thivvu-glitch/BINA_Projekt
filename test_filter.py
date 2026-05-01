import pandas as pd

def teste_turnier_filter():
    print("Lade Daten für den Test...")
    df_events = pd.read_csv('Data/game_events.csv', usecols=['game_id', 'player_id'])
    df_games = pd.read_csv('Data/games.csv', usecols=['game_id', 'competition_id', 'season'])
    df_players = pd.read_csv('Data/players.csv', usecols=['player_id', 'name'])
    df_injuries = pd.read_csv('Data/cleaned_dataset_final.csv')

    # Filtern der Spiele nach spezifischem Turnier (anhand der Saison in games.csv)
    euro2020_games = df_games[(df_games['competition_id'] == 'EURO') & (df_games['season'] == 2020)]['game_id'].unique()
    wm2022_games = df_games[df_games['competition_id'] == 'FIWC']['game_id'].unique()
    euro2024_games = df_games[(df_games['competition_id'] == 'EURO') & (df_games['season'] == 2023)]['game_id'].unique()

    # Spieler-IDs extrahieren
    euro2020_pids = df_events[df_events['game_id'].isin(euro2020_games)]['player_id'].dropna().unique()
    wm2022_pids = df_events[df_events['game_id'].isin(wm2022_games)]['player_id'].dropna().unique()
    euro2024_pids = df_events[df_events['game_id'].isin(euro2024_games)]['player_id'].dropna().unique()

    # Namen extrahieren
    euro2020_names = set(df_players[df_players['player_id'].isin(euro2020_pids)]['name'].unique())
    wm2022_names = set(df_players[df_players['player_id'].isin(wm2022_pids)]['name'].unique())
    euro2024_names = set(df_players[df_players['player_id'].isin(euro2024_pids)]['name'].unique())

    # Verletzungen für diese Spieler filtern
    inj_euro2020 = df_injuries[df_injuries['player_name'].isin(euro2020_names)]
    inj_wm2022 = df_injuries[df_injuries['player_name'].isin(wm2022_names)]
    inj_euro2024 = df_injuries[df_injuries['player_name'].isin(euro2024_names)]

    def print_turnier_stats(t_name, p_names, inj_df):
        total_players = len(p_names)
        players_with_inj = inj_df['player_name'].nunique()
        total_injuries = len(inj_df)
        
        print(f"\n=========================================")
        print(f" {t_name}")
        print(f"=========================================")
        print(f"Es gingen insgesamt {total_players} Spieler an dieses Turnier.")
        print(f"Davon haben sich {players_with_inj} Spieler (innerhalb von 2020-2025) mindestens einmal verletzt.")
        print(f"Diese {players_with_inj} verletzten Spieler sammelten insgesamt {total_injuries} Verletzungen.")
        
        print("\nAufteilung dieser Verletzungen nach Saisons:")
        grouped = inj_df.groupby('Season').size()
        for season, count in grouped.items():
            print(f"  -> Saison {season}: {count} Verletzungen")

    print_turnier_stats("EURO 2020 (Gespielt im Sommer 2021)", euro2020_names, inj_euro2020)
    print_turnier_stats("WM 2022 (Gespielt im Winter 2022 in Katar)", wm2022_names, inj_wm2022)
    print_turnier_stats("EURO 2024 (Gespielt im Sommer 2024)", euro2024_names, inj_euro2024)

if __name__ == "__main__":
    teste_turnier_filter()
