import pandas as pd
import random

players_info_df = pd.read_csv('Data/players.csv')
players_a = players_info_df['name'].head(500).tolist()
players_b_pool = players_info_df['name'].tail(2000).tolist()

df_a_info = players_info_df[players_info_df['name'].isin(players_a)].copy()
df_b_info = players_info_df[players_info_df['name'].isin(players_b_pool)].copy()

df_a_info['current_club_domestic_competition_id'] = df_a_info['current_club_domestic_competition_id'].fillna('Unknown')
df_a_info['position'] = df_a_info['position'].fillna('Unknown')
df_b_info['current_club_domestic_competition_id'] = df_b_info['current_club_domestic_competition_id'].fillna('Unknown')
df_b_info['position'] = df_b_info['position'].fillna('Unknown')

strata_counts = df_a_info.groupby(['current_club_domestic_competition_id', 'position']).size().to_dict()
print(list(strata_counts.items())[:3])

sampled_b_names = []
for (league, pos), count in strata_counts.items():
    pool_for_stratum = df_b_info[(df_b_info['current_club_domestic_competition_id'] == league) & (df_b_info['position'] == pos)]['name'].tolist()
    if len(pool_for_stratum) >= count:
        sampled_b_names.extend(random.sample(pool_for_stratum, count))
    else:
        sampled_b_names.extend(pool_for_stratum)

print(f"Needed: {len(players_a)}, Matched exact: {len(sampled_b_names)}")
