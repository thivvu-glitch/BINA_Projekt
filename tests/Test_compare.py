import pandas as pd
import numpy as np

# 1. Daten laden
print("Lade Datensätze...")
dfInjuries = pd.read_csv('./Data/full_dataset_thesis - 1.csv', encoding='utf-8')
dfPlayers = pd.read_csv('./Data/players.csv', encoding='utf-8')

# Namen bereinigen
dfInjuries['player_name'] = dfInjuries['player_name'].astype(str).str.strip()
dfPlayers['name'] = dfPlayers['name'].astype(str).str.strip()

# Verletzungsjahr & Geburtsjahr extrahieren
dfInjuries['injury_year'] = pd.to_datetime(dfInjuries['injury_from_parsed'], errors='coerce').dt.year
dfPlayers['birth_year'] = pd.to_datetime(dfPlayers['date_of_birth'], errors='coerce').dt.year

# Eindeutige ID für jede Verletzung
dfInjuries['injury_id'] = range(len(dfInjuries))

# Finde alle Namen, die in players.csv MEHRFACH vorkommen (Konflikte)
duplicate_player_names = dfPlayers[dfPlayers['name'].duplicated()]['name'].unique()

# Mergen aller Kombinationen (Kartesisches Produkt für gleiche Namen)
merged_df = pd.merge(
    dfInjuries, 
    dfPlayers[['name', 'player_id', 'birth_year', 'last_season', 'current_club_name', 'market_value_in_eur']], 
    left_on='player_name', 
    right_on='name', 
    how='left'
)

# Berechne Altersdifferenz
merged_df['expected_birth_year'] = merged_df['injury_year'] - merged_df['player_age']
merged_df['age_diff'] = abs(merged_df['birth_year'] - merged_df['expected_birth_year']).fillna(999)

# Finde für jede injury_id den besten Match (geringste Altersdifferenz)
best_matches = merged_df.sort_values(['injury_id', 'age_diff']).drop_duplicates(subset=['injury_id'], keep='first')
best_matches_ids = set(best_matches['player_id'])

# Wir erstellen einen zusammenfassenden Bericht gruppiert nach SPIELER-NAMEN
summary_lines = []
summary_lines.append("================================================================================")
summary_lines.append("             ZUSAMMENFASSUNG: NAMENSKONFLIKTE PRO SPIELER")
summary_lines.append("================================================================================")
summary_lines.append("Hier siehst du für jeden doppelt vorkommenden Namen, welcher Spieler")
summary_lines.append("tatsächlich mit den Verletzungen verknüpft wurde und welcher ignoriert wurde.\n\n")

print(f"Generiere Zusammenfassung für {len(duplicate_player_names)} betroffene Namen...\n")

conflict_players_count = 0

for name in sorted(duplicate_player_names):
    # Alle Kandidaten für diesen Namen in players.csv
    candidates = dfPlayers[dfPlayers['name'] == name]
    
    # Alle Verletzungen für diesen Namen in injuries
    player_injuries = dfInjuries[dfInjuries['player_name'] == name]
    if len(player_injuries) == 0:
        continue # Keine Verletzungen für diesen Namen im Datensatz
        
    conflict_players_count += 1
    
    summary_lines.append(f"=== SPIELER: {name} (Gesamte Verletzungen im Datensatz: {len(player_injuries)}) ===")
    
    # Für jeden Kandidaten prüfen, wie viele Verletzungen ihm zugeordnet wurden
    for _, candidate in candidates.iterrows():
        pid = candidate['player_id']
        birth_y = candidate['birth_year']
        club = candidate['current_club_name']
        mv = f"{candidate['market_value_in_eur']/1000000:.1f} Mio. €" if pd.notna(candidate['market_value_in_eur']) else "Unbekannt"
        
        # Wie viele Verletzungen dieses Namens wurden dieser ID zugeordnet?
        assigned_injuries = best_matches[(best_matches['player_name'] == name) & (best_matches['player_id'] == pid)]
        assigned_count = len(assigned_injuries)
        
        if assigned_count > 0:
            status = f"[AKZEPTIERT] -> Zugewiesen: {assigned_count} Verletzung(en)"
            # Zeige die Saisons der zugewiesenen Verletzungen
            seasons = sorted(assigned_injuries['Season'].unique().tolist())
            season_str = f" (Saisons: {', '.join(seasons)})"
        else:
            status = "[ABGELEHNT]  -> Gelöscht / Ignoriert (0 Verletzungen zugeordnet)"
            season_str = ""
            
        summary_lines.append(f"  * ID {int(pid)} | Geboren: {int(birth_y) if pd.notna(birth_y) else 'Unbekannt'} | Verein: {club} ({mv})")
        summary_lines.append(f"    Status: {status}{season_str}")
        
    summary_lines.append("\n" + "-"*80 + "\n")

# In Datei schreiben
report_file = 'conflict_resolution_summary.txt'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(summary_lines))

# Ein paar Highlights in der Konsole ausgeben
print("=== EINIGE HIGHLIGHTS AUS DER ZUSAMMENFASSUNG ===")
highlight_names = ['Aaron Ramsey', 'Bruno Alves', 'Claudio Bravo', 'Paulinho', 'Vitinho']
for name in highlight_names:
    if name in duplicate_player_names:
        print(f"\nSpieler: {name}")
        candidates = dfPlayers[dfPlayers['name'] == name]
        for _, candidate in candidates.iterrows():
            pid = candidate['player_id']
            assigned_count = len(best_matches[(best_matches['player_name'] == name) & (best_matches['player_id'] == pid)])
            status = "AKZEPTIERT" if assigned_count > 0 else "IGNORIERT"
            print(f"  - ID {int(pid)} (Geb. {int(candidate['birth_year']) if pd.notna(candidate['birth_year']) else 'Unbekannt'}): {status} ({assigned_count} Verletzungen)")

print(f"\nDer zusammenfassende Bericht für alle {conflict_players_count} Spieler wurde gespeichert in: {report_file}")
print("Öffne 'conflict_resolution_summary.txt' in deinem Editor, um die komplette Liste zu sehen!")
