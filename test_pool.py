import pandas as pd
import random
import sys
from datetime import datetime

def get_mv_tier(val):
    if pd.isna(val):
        return 'Unknown'
    if val >= 40000000:
        return 'Tier 1 (>40M)'
    elif val >= 10000000:
        return 'Tier 2 (10M-40M)'
    else:
        return 'Tier 3 (<10M)'

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

def test_matching(player_name):
    # 1. Daten laden
    try:
        df = pd.read_csv('Data/players.csv')
    except Exception as e:
        print(f"Fehler beim Laden der Daten: {e}")
        return
        
    # Fehlende Werte behandeln
    df['current_club_domestic_competition_id'] = df['current_club_domestic_competition_id'].fillna('Unknown')
    df['position'] = df['position'].fillna('Unknown')
    
    # Tiers zuweisen
    df['mv_tier'] = df['market_value_in_eur'].apply(get_mv_tier)
    df['age_tier'] = df['date_of_birth'].apply(get_age_tier)
    
    # 2. Den gesuchten Spieler finden
    player_data = df[df['name'].str.contains(player_name, case=False, na=False)]
    if player_data.empty:
        print(f"Spieler '{player_name}' nicht gefunden!")
        return
        
    p = player_data.iloc[0]
    p_league = p['current_club_domestic_competition_id']
    p_pos = p['position']
    p_tier = p['mv_tier']
    p_mv = p['market_value_in_eur']
    p_age_tier = p['age_tier']
    p_dob = p['date_of_birth']
    
    print("=" * 70)
    print(f"🔍 ZUR ANALYSE AUSGEWÄHLTER SPIELER:")
    print(f"Name:       {p['name']}")
    print(f"Liga:       {p_league}")
    print(f"Position:   {p_pos} (Spezifisch: {p['sub_position']})")
    print(f"Marktwert:  {p_mv:,.0f} € ({p_tier})")
    print(f"Alter:      Jahrgang {str(p_dob)[:4]} ({p_age_tier})")
    print("=" * 70)
    
    # 3. Den Pool der potenziellen Vergleichsspieler definieren
    pool_df = df[df['name'] != p['name']]
    
    # 4. Nach exakten Matches suchen
    exact_matches = pool_df[
        (pool_df['current_club_domestic_competition_id'] == p_league) & 
        (pool_df['position'] == p_pos) & 
        (pool_df['mv_tier'] == p_tier) &
        (pool_df['age_tier'] == p_age_tier)
    ]
    
    print(f"\n✅ {len(exact_matches)} EXAKTE Matches gefunden (Gleiche Liga, grobe Position, gleiches MV-Tier, gleiches Alters-Tier):")
    if not exact_matches.empty:
        sample_size = min(5, len(exact_matches))
        samples = exact_matches.sample(sample_size)
        for _, match in samples.iterrows():
            print(f"   - {match['name']:<20} | MV: {match['market_value_in_eur']:>11,.0f} € | Alter: {match['age_tier']}")
            
    # 5. Fallback 1: Richtiges Alter, aber anderes Geld
    fallback_1_matches = pool_df[
        (pool_df['current_club_domestic_competition_id'] == p_league) & 
        (pool_df['position'] == p_pos) & 
        (pool_df['age_tier'] == p_age_tier) &
        (pool_df['mv_tier'] != p_tier) 
    ]
    
    print(f"\n⚠️ {len(fallback_1_matches)} FALLBACK 1 Matches gefunden (Gleiches Alter, ABER anderer Marktwert):")
    if not fallback_1_matches.empty:
        sample_size = min(5, len(fallback_1_matches))
        samples = fallback_1_matches.sample(sample_size)
        for _, match in samples.iterrows():
            print(f"   - {match['name']:<20} | MV: {match['market_value_in_eur']:>11,.0f} € ({match['mv_tier']})")

    # 6. Fallback 2: Alles falsch außer Liga & Position
    fallback_2_matches = pool_df[
        (pool_df['current_club_domestic_competition_id'] == p_league) & 
        (pool_df['position'] == p_pos) & 
        (pool_df['age_tier'] != p_age_tier)
    ]
    print(f"\n🆘 {len(fallback_2_matches)} FALLBACK 2 Matches gefunden (Nur gleiche Liga & Position. Alter/Geld ist komplett abweichend):")
    
    print("\n" + "=" * 70)
    print("💡 FAZIT FÜR DEN ALGORITHMUS:")
    if len(exact_matches) > 0:
        print("Der Algorithmus zieht zufällig einen der EXAKTEN Matches als Zwilling für die Kontrollgruppe.")
    elif len(fallback_1_matches) > 0:
        print("Da es keine exakten Matches gibt, greift der Algorithmus auf FALLBACK 1 zurück (Alter priorisiert über Geld).")
    else:
        print("Kein Alter / Geld Match. Der Algorithmus nimmt einfach irgendeinen Spieler auf der Position in dieser Liga.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_name = " ".join(sys.argv[1:])
    else:
        search_name = "Jamal Musiala" # Default Test
        print("Kein Spieler angegeben, teste mit 'Jamal Musiala'...\n")
        
    test_matching(search_name)
