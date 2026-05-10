import pandas as pd
import numpy as np

# Lade Daten
dfInjuries = pd.read_csv('./Data/full_dataset_thesis - 1.csv', encoding='utf-8')
dfPlayers = pd.read_csv('./Data/players.csv', encoding='utf-8')

# Bereinige Namen (wie in data_clean.py)
dfInjuries['player_name'] = dfInjuries['player_name'].astype(str).str.strip()
dfPlayers['name'] = dfPlayers['name'].astype(str).str.strip()

# Füge eindeutige ID zu Verletzungen hinzu, damit wir später auf 1 pro Verletzung reduzieren können
dfInjuries['injury_id'] = range(len(dfInjuries))

# Extrahieren des Verletzungsjahres
dfInjuries['injury_year'] = pd.to_datetime(dfInjuries['injury_from_parsed'], errors='coerce').dt.year

# Extrahieren des Geburtsjahres
dfPlayers['birth_year'] = pd.to_datetime(dfPlayers['date_of_birth'], errors='coerce').dt.year

# Mache einen expliziten FULL LEFT MERGE auf den Namen
# (Achtung: Dies erzeugt kurzzeitig Duplikate bei Spielern mit Namensgleichheit)
merged_df = pd.merge(
    dfInjuries, 
    dfPlayers[['name', 'market_value_in_eur', 'birth_year', 'last_season']], 
    left_on='player_name', 
    right_on='name', 
    how='left'
)

# Berechne das theoretische Alter des Spielers zum Verletzungszeitpunkt
merged_df['expected_age'] = merged_df['injury_year'] - merged_df['birth_year']

# Berechne die absolute Abweichung zwischen dem theoretischen Alter und dem in den Daten angegebenen player_age
# fillna(999) für Spieler, die in players.csv gar nicht gefunden wurden (oder kein Geburtsdatum haben)
merged_df['age_diff'] = abs(merged_df['expected_age'] - merged_df['player_age']).fillna(999)

# Wende einen kleinen Penalty an, wenn das injury_year > last_season ist 
# (Das bedeutet, der Spieler hatte eigentlich schon aufgehört oder war nicht mehr in der Liga)
merged_df['season_penalty'] = np.where(merged_df['injury_year'] > merged_df['last_season'] + 1, 100, 0)
merged_df['total_score'] = merged_df['age_diff'] + merged_df['season_penalty']

# Sortiere nach score (niedrigster = bester Match)
merged_df = merged_df.sort_values('total_score', ascending=True)

# Behalte pro Verletzung (injury_id) genau EINEN Treffer (den besten)
final_df = merged_df.drop_duplicates(subset=['injury_id'], keep='first')

print("Anzahl Ursprungs-Verletzungen: ", len(dfInjuries))
print("Anzahl gemergte Verletzungen (nach Filter): ", len(final_df))
print("Erste Zeilen des finalen DFs:")
print(final_df[['player_name', 'player_age', 'birth_year', 'expected_age', 'age_diff']].head(5))
