import pandas as pd
import numpy as np

dfInjuries = pd.read_csv('./Data/full_dataset_thesis - 1.csv')
dfPlayers = pd.read_csv('./Data/players.csv')

# Parse season to year
def parse_season(s):
    if pd.isna(s): return np.nan
    try:
        parts = str(s).split('/')
        if len(parts) > 0:
            val = int(parts[0])
            return 2000 + val if val < 50 else 1900 + val
    except:
        pass
    return np.nan

dfInjuries['injury_year'] = dfInjuries['Season'].apply(parse_season)
dfPlayers['birth_year'] = pd.to_datetime(dfPlayers['date_of_birth'], errors='coerce').dt.year

# Let's find a player name that is duplicated in players.csv
duplicates = dfPlayers[dfPlayers.duplicated(subset=['name'], keep=False)]
dup_names = duplicates['name'].unique()

print(f"Found {len(dup_names)} duplicate names in players.csv.")

# Let's test merging for one specific duplicate name, e.g., 'Bruno Alves'
sample_name = 'Bruno Alves'
inj = dfInjuries[dfInjuries['player_name'] == sample_name].head(1)
pl = dfPlayers[dfPlayers['name'] == sample_name]

print("\nInjury:")
print(inj[['player_name', 'player_age', 'injury_year']])
print("\nPlayers:")
print(pl[['name', 'birth_year', 'last_season', 'market_value_in_eur']])

