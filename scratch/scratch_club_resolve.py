import pandas as pd
import numpy as np

# Load Data
print("Loading data...")
dfInjuries = pd.read_csv('./Data/full_dataset_thesis - 1.csv', encoding='utf-8')
dfPlayers = pd.read_csv('./Data/players.csv', encoding='utf-8')
dfVals = pd.read_csv('./Data/player_valuations.csv', encoding='utf-8')

print("Preparing data...")
dfVals['date'] = pd.to_datetime(dfVals['date'])
dfVals = dfVals.sort_values('date')

# 1. Standardize and age validation (simplified)
dfInjuries['injury_from_parsed'] = pd.to_datetime(dfInjuries['injury_from_parsed'], errors='coerce')
dfInjuries['injury_year'] = dfInjuries['injury_from_parsed'].dt.year
dfInjuries['calculated_birth_year'] = dfInjuries['injury_year'] - pd.to_numeric(dfInjuries['player_age'], errors='coerce')
dfInjuries['temp_orig_id'] = range(len(dfInjuries))

dfPlayers['player_birth_year'] = pd.to_datetime(dfPlayers['date_of_birth'], errors='coerce').dt.year

df = pd.merge(dfInjuries, dfPlayers[['name', 'player_id', 'player_birth_year']], left_on='player_name', right_on='name', how='left')
df['age_diff'] = (df['player_birth_year'] - df['calculated_birth_year']).abs()
df = df.sort_values(by=['temp_orig_id', 'age_diff'])
df = df.drop_duplicates(subset=['temp_orig_id'], keep='first')

# 2. Resolve Category 2 Duplicates (same player, same injury, same date, DIFFERENT club)
# We need to find the true club for each injury
print("Resolving clubs via valuations...")
df_sorted = df.sort_values('injury_from_parsed').dropna(subset=['injury_from_parsed'])

# merge_asof requires sorted left and right on the merge key
result = pd.merge_asof(
    df_sorted, 
    dfVals[['player_id', 'date', 'current_club_name']].dropna(), 
    left_on='injury_from_parsed', 
    right_on='date', 
    by='player_id', 
    direction='nearest'
)

# Calculate club match score
def club_match(row):
    if pd.isna(row['current_club_name']) or pd.isna(row['club']):
        return 0
    c1 = str(row['club']).lower().replace(' ', '')
    c2 = str(row['current_club_name']).lower().replace(' ', '')
    if c1 in c2 or c2 in c1:
        return 1
    return 0

result['club_match_score'] = result.apply(club_match, axis=1)

# Now, group by the duplicate criteria
subset_dup = ['player_name', 'Injury', 'injury_from_parsed']

# Sort so that highest club_match_score is first
result = result.sort_values(by=subset_dup + ['club_match_score'], ascending=[True, True, True, False])

dupes_before = result.duplicated(subset=subset_dup, keep=False).sum()
print(f"Duplicates before dropping: {dupes_before}")

result_final = result.drop_duplicates(subset=subset_dup, keep='first')

dupes_after = result_final.duplicated(subset=subset_dup, keep=False).sum()
print(f"Duplicates after dropping: {dupes_after}")

print("Aaron Ramsdale test:")
print(result_final[result_final['player_name'] == 'Aaron Ramsdale'][['Injury', 'injury_from_parsed', 'club', 'current_club_name', 'club_match_score']])

print("Abdou Diallo test:")
print(result_final[(result_final['player_name'] == 'Abdou Diallo') & (result_final['injury_from_parsed'] == '2023-01-23')][['Injury', 'injury_from_parsed', 'club', 'current_club_name', 'club_match_score']])
