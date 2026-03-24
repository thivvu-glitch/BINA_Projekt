import pandas as pd

# 1. Daten laden
df = pd.read_csv('./Data/full_dataset_thesis - 1.csv')

# 2. Bereinigung der 'Days'-Spalte (z.B. "10 days" -> 10, "-" -> 0)
df['Days'] = df['Days'].str.replace(' days', '').str.replace('-', '0').fillna('0')
df['Days'] = pd.to_numeric(df['Days'], errors='coerce').fillna(0).astype(int)

# 3. Textspalten standardisieren (Leerzeichen entfernen)
text_cols = ['Injury', 'player_name', 'player_position', 'club', 'league']
for col in text_cols:
    df[col] = df[col].astype(str).str.strip()

# 4. Kodierungsfehler beheben
def fix_encoding(text):
    if pd.isna(text):
        return text
    # Häufige UTF-8-Fehlinterpretationen korrigieren
    replacements = {
        'Ã©': 'é', 'Ã¡': 'á', 'Ã³': 'ó', 
        'Ã¼': 'ü', 'Ã¶': 'ö', 'Ã¤': 'ä',
        'Â': ''
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    return text

for col in text_cols:
    df[col] = df[col].apply(fix_encoding)

# 5. Konsistenz der Vereinsnamen (z. B. Köln -> FC Köln)
club_mapping = {
    'Köln': 'FC Köln',
    'Mainz': 'Mainz 05',
    'Bayern Munich': 'Bayern München',
    'RB Leipzig': 'RB Leipzig',
    'Bochum': 'VfL Bochum',
    'Dortmund': 'Borussia Dortmund',
    'Schalke': 'FC Schalke 04',
    'Leverkusen': 'Bayer Leverkusen',
    'Tottenham': 'Tottenham Hotspur',
    'Koln': 'FC Köln',
    'West Ham': 'West Ham United',
    'Wolfsburg': 'VfL Wolfsburg',
    'Stuttgart': 'VfB Stuttgart',
    'Greuther Furth': 'Greuther Fürth',
    'Hertha Berlin': 'Hertha BSC',
    'Freiburg': 'SC Freiburg',
    'Schalke 04': 'FC Schalke 04',
    'FC Koln': 'FC Köln',
    'Borussia Monchengladbach': 'Borussia Mönchengladbach',
}
df['club'] = df['club'].replace(club_mapping)

# 6. Verletzungen vereinheitlichen (Kleinschreibung)
df['Injury'] = df['Injury'].str.lower()


# 7. Bereinigte Daten speichern
df.to_csv('./Data/cleaned_dataset_final.csv', index=False)

print("Bereinigung abgeschlossen. Datei gespeichert unter: cleaned_dataset_final.csv")

# Optional: Checks durchführen
#print(sorted(df['club'].unique()))
#print(sorted(df['player_name'].unique()))