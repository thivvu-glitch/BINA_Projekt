import pandas as pd

dfInjuries = pd.read_csv('./Data/full_dataset_thesis - 1.csv', encoding='utf-8')
dfPlayers = pd.read_csv('./Data/players.csv', encoding='utf-8')

dfInjuries['temp_id'] = range(len(dfInjuries))
print(f"Original injuries: {len(dfInjuries)}")

df_merged = pd.merge(dfInjuries, dfPlayers[['name', 'market_value_in_eur', 'date_of_birth']], left_on='player_name', right_on='name', how='left')
print(f"Merged without filtering: {len(df_merged)}")

df_merged['player_birth_year'] = pd.to_datetime(df_merged['date_of_birth'], errors='coerce').dt.year
df_merged['injury_year'] = pd.to_datetime(df_merged['injury_from_parsed'], errors='coerce').dt.year
df_merged['calculated_birth_year'] = df_merged['injury_year'] - df_merged['player_age']
df_merged['age_diff'] = abs(df_merged['player_birth_year'] - df_merged['calculated_birth_year'])

df_merged = df_merged.sort_values(by=['temp_id', 'age_diff'])
df_final = df_merged.drop_duplicates(subset=['temp_id'], keep='first')
print(f"Final injuries after age validation: {len(df_final)}")
