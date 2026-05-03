import pandas as pd
import random
from datetime import datetime

# Daten laden
players_info_df = pd.read_csv('Data/players.csv')
players_a = players_info_df['name'].head(500).tolist()
players_b_pool = players_info_df['name'].tail(2000).tolist()

df_a_info = players_info_df[players_info_df['name'].isin(players_a)].copy()
df_b_info = players_info_df[players_info_df['name'].isin(players_b_pool)].copy()

# 1. Fehlende Werte füllen
df_a_info['current_club_domestic_competition_id'] = df_a_info['current_club_domestic_competition_id'].fillna('Unknown')
df_a_info['position'] = df_a_info['position'].fillna('Unknown')
df_b_info['current_club_domestic_competition_id'] = df_b_info['current_club_domestic_competition_id'].fillna('Unknown')
df_b_info['position'] = df_b_info['position'].fillna('Unknown')

# 2. Marktwert-Buckets (Tiers) erstellen
def get_mv_tier(val):
    if pd.isna(val):
        return 'Unknown'
    if val >= 40000000:
        return 'Tier 1 (>40M)'
    elif val >= 10000000:
        return 'Tier 2 (10M-40M)'
    else:
        return 'Tier 3 (<10M)'

# 2.5 Alters-Buckets (Age Tiers) erstellen
def get_age_tier(dob_str):
    if pd.isna(dob_str):
        return 'Unknown'
    try:
        birth_year = int(str(dob_str)[:4])
        age = 2024 - birth_year # Referenzjahr 2024
        if age <= 23:
            return 'Talent (U23)'
        elif age <= 28:
            return 'Peak (24-28)'
        else:
            return 'Veteran (Ü28)'
    except:
        return 'Unknown'

df_a_info['mv_tier'] = df_a_info['market_value_in_eur'].apply(get_mv_tier)
df_b_info['mv_tier'] = df_b_info['market_value_in_eur'].apply(get_mv_tier)

df_a_info['age_tier'] = df_a_info['date_of_birth'].apply(get_age_tier)
df_b_info['age_tier'] = df_b_info['date_of_birth'].apply(get_age_tier)

# 3. Strata definieren (Liga + Position + Marktwert-Tier + Alters-Tier)
strata_counts = df_a_info.groupby(['current_club_domestic_competition_id', 'position', 'mv_tier', 'age_tier']).size().to_dict()

print("Beispielhafte Strata (Liga, Position, Marktwert-Tier, Alters-Tier):")
print(list(strata_counts.items())[:3])
print("-" * 30)

# 4. Matching mit Fallback-Logik
sampled_b_names = []
for (league, pos, mv_tier, age_tier), count in strata_counts.items():
    # Versuch 1: Exaktes Match (Liga + Position + Tier + Alter)
    exact_pool = df_b_info[
        (df_b_info['current_club_domestic_competition_id'] == league) & 
        (df_b_info['position'] == pos) & 
        (df_b_info['mv_tier'] == mv_tier) &
        (df_b_info['age_tier'] == age_tier)
    ]['name'].tolist()
    
    if len(exact_pool) >= count:
        sampled_b_names.extend(random.sample(exact_pool, count))
    else:
        sampled_b_names.extend(exact_pool)
        needed_more = count - len(exact_pool)
        
        # Fallback 1: Gleiche Liga, Position und Alter (Marktwert egal)
        fallback_1_pool = df_b_info[
            (df_b_info['current_club_domestic_competition_id'] == league) & 
            (df_b_info['position'] == pos) &
            (df_b_info['age_tier'] == age_tier)
        ]['name'].tolist()
        
        available_f1 = list(set(fallback_1_pool) - set(exact_pool))
        
        if len(available_f1) >= needed_more:
            sampled_b_names.extend(random.sample(available_f1, needed_more))
        else:
            sampled_b_names.extend(available_f1)
            needed_more -= len(available_f1)
            
            # Fallback 2: Nur Liga und Position (Alter und Marktwert egal)
            fallback_2_pool = df_b_info[
                (df_b_info['current_club_domestic_competition_id'] == league) & 
                (df_b_info['position'] == pos)
            ]['name'].tolist()
            
            available_f2 = list(set(fallback_2_pool) - set(exact_pool) - set(available_f1))
            
            if len(available_f2) >= needed_more:
                sampled_b_names.extend(random.sample(available_f2, needed_more))
            else:
                sampled_b_names.extend(available_f2)

print(f"Benötigte Kontroll-Spieler: {len(players_a)}")
print(f"Gefundene gematchte Spieler: {len(sampled_b_names)}")
