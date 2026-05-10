import pandas as pd

# 1. Daten laden
dfInjuries = pd.read_csv('./Data/full_dataset_thesis - 1.csv', encoding='utf-8')
dfPlayers = pd.read_csv('./Data/players.csv', encoding='utf-8')
dfVals = pd.read_csv('./Data/player_valuations.csv', encoding='utf-8')
dfVals['date'] = pd.to_datetime(dfVals['date'])
dfVals = dfVals.sort_values('date')

# 2. Bereinigung der 'Days'-Spalte (z. B. "10 days" -> 10, "-" -> 0)
dfInjuries['Days'] = dfInjuries['Days'].str.replace(' days', '').str.replace('-', '0').fillna('0')
dfInjuries['Days'] = pd.to_numeric(dfInjuries['Days'], errors='coerce').fillna(0).astype(int)

# 3. Textspalten standardisieren (Leerzeichen entfernen)
text_colsInjuries = ['Injury', 'player_name', 'player_position', 'club', 'league']
for col in text_colsInjuries:
    dfInjuries[col] = dfInjuries[col].astype(str).str.strip()

text_colsPlayers = ['name']
for col in text_colsPlayers:
    dfPlayers[col] = dfPlayers[col].astype(str).str.strip()

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

for col in text_colsInjuries:
    dfInjuries[col] = dfInjuries[col].apply(fix_encoding)

for col in text_colsPlayers:
    dfPlayers[col] = dfPlayers[col].apply(fix_encoding)

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
    'Roma': 'AS Roma',
    'Verona': 'Hellas Verona',
}
dfInjuries['club'] = dfInjuries['club'].replace(club_mapping)

# 6. Verletzungen vereinheitlichen (Kleinschreibung)
dfInjuries['Injury'] = dfInjuries['Injury'].str.lower()

# 8. Kategorisierung der Verletzungen
injury_map = {

    # ---------------- HEAD / NECK ----------------
    "concussion": "Head",
    "head injury": "Head",
    "eye injury": "Head",
    "facial injury": "Head",
    "broken nose bone": "Head",
    "neck injury": "Neck",
    "neck problems": "Neck",

    # ---------------- SHOULDER ----------------
    "shoulder injury": "Shoulder",
    "shoulder problems": "Shoulder",

    # ---------------- CHEST / RIBS ----------------
    "rib fracture": "Chest/Ribs",
    "bruised ribs": "Chest/Ribs",
    "chest injury": "Chest/Ribs",

    # ---------------- BACK / SPINE ----------------
    "back problems": "Back/Spine",
    "back injury": "Back/Spine",
    "herniated disc": "Back/Spine",
    "lumbago": "Back/Spine",
    "cervical spine injury": "Back/Spine",
    "compression of the spine": "Back/Spine",
    "lumbar vertebra fracture": "Back/Spine",

    # ---------------- ABDOMEN / CORE ----------------
    "abdominal problems": "Abdomen/Core",
    "abdominal injury": "Abdomen/Core",
    "stomach problems": "Abdomen/Core",

    # ---------------- HIP / GROIN ----------------
    "groin injury": "Hip/Groin",
    "groin problems": "Hip/Groin",
    "pubalgia": "Hip/Groin",
    "groin surgery": "Hip/Groin",
    "hip injury": "Hip/Groin",
    "hip problems": "Hip/Groin",
    "adductor pain": "Hip/Groin",
    "adductor injury": "Hip/Groin",
    "adductor strain": "Hip/Groin",
    "inflammation of pubic bone": "Hip/Groin",

    # ---------------- UPPER ARM ----------------
    "upper arm injury": "Upper Arm",
    "arm injury": "Upper Arm",
    "broken arm": "Upper Arm",

    # ---------------- ELBOW ----------------
    "elbow injury": "Elbow",
    "elbow problems": "Elbow",

    # ---------------- FOREARM ----------------
    "forearm fracture": "Forearm",
    "forearm injury": "Forearm",

    # ---------------- HAND / FINGER ----------------
    "hand injury": "Hand/Finger",
    "broken hand": "Hand/Finger",
    "broken finger": "Hand/Finger",

    # ---------------- THIGH ----------------
    "torn muscle fiber": "Thigh",
    "torn muscle bundle": "Thigh",
    "hamstring injury": "Thigh",
    "hamstring strain": "Thigh",
    "hamstring muscle injury": "Thigh",
    "muscle strain": "Thigh",
    "muscle tear": "Thigh",
    "partial muscle tear": "Thigh",
    "torn thigh muscle": "Thigh",
    "muscle contusion": "Thigh",
    "thigh problems": "Thigh",
    "dead leg": "Thigh",
    "leg injury": "Thigh",
    "strain": "Thigh",

    # ---------------- KNEE ----------------
    "knee injury": "Knee",
    "knee problems": "Knee",
    "knee surgery": "Knee",
    "meniscus damage": "Knee",
    "meniscus tear": "Knee",
    "meniscus injury": "Knee",
    "meniscus irritation": "Knee",
    "cartilage damage": "Knee",
    "patellar tendon problems": "Knee",
    "patellar tendon rupture": "Knee",
    "patellar tendon tear": "Knee",
    "patellar tendinopathy syndrome": "Knee",
    "knee bruise": "Knee",
    "cruciate ligament tear": "Knee",
    "cruciate ligament injury": "Knee",
    "cruciate ligament strain": "Knee",
    "inner ligament injury": "Knee",
    "inner ligament tear": "Knee",
    "collateral ligament tear": "Knee",
    "collateral ligament injury": "Knee",

    # ---------------- LOWER LEG ----------------
    "calf injury": "Lower Leg",
    "calf strain": "Lower Leg",
    "calf muscle tear": "Lower Leg",
    "calf problems": "Lower Leg",
    "achilles tendon injury": "Lower Leg",
    "achilles tendon problems": "Lower Leg",
    "achilles tendon rupture": "Lower Leg",
    "broken fibula": "Lower Leg",
    "broken leg": "Lower Leg",

    # ---------------- ANKLE ----------------
    "ankle injury": "Ankle",
    "ankle problems": "Ankle",
    "ankle sprain": "Ankle",
    "injury to the ankle": "Ankle",
    "ankle ligament tear": "Ankle",
    "torn ankle ligaments": "Ankle",
    "syndesmosis ligament tear": "Ankle",
    "syndesmotic ligament tear": "Ankle",
    "ligament stretching": "Ankle",
    "broken ankle": "Ankle",
    "ankle surgery": "Ankle",

    # ---------------- FOOT / TOE ----------------
    "foot injury": "Foot/Toe",
    "broken foot": "Foot/Toe",
    "metatarsal fracture": "Foot/Toe",
    "broken toe": "Foot/Toe",
    "toe injury": "Foot/Toe",
    "heel problems": "Foot/Toe",
    "heel injury": "Foot/Toe",
    "hairline crack in foot": "Foot/Toe",
    "fatigue fracture": "Foot/Toe",
    "foot surgery": "Foot/Toe",

    # ---------------- GENERIC MUSCLE ----------------
    "muscle injury": "Muscle",
    "muscular problems": "Muscle",
    "muscle stiffness": "Muscle",
    "muscle fatigue": "Muscle",
    "sore muscles": "Muscle",

    # ---------------- GENERIC FRACTURE ----------------
    "fracture": "Bone",
    
    # ---------------- GENERIC LIGAMENT ----------------
    "ligament injury": "Ligament",
    "ligament tear": "Ligament",
    "torn ligaments": "Ligament",
    
    # ---------------- SURGERY ----------------
    "surgery": "Surgery",
    "dental surgery": "Surgery",
    "arthroscopy": "Surgery",
    
    # ---------------- ILLNESS ----------------
    "corona virus": "Illness",
    "virus": "Illness",
    "cold": "Illness",
    "flu": "Illness",
    "influenza": "Illness",
    "fever": "Illness",
    "infection": "Illness",
    "bronchitis": "Illness",
    "pneumonia": "Illness",
    "stomach flu": "Illness",
    "intestinal virus": "Illness",
    "tonsillitis": "Illness",
    "ill": "Illness", 
    
    # ---------------- MINOR / GENERIC ----------------
    "minor knock": "Minor",
    "knock": "Minor",
    "bruise": "Minor",
    "bone bruise": "Minor",
    "inflammation": "Minor",

    # ---------------- NON-INJURY ----------------
    "fitness": "Non-injury",
    "rest": "Non-injury",
    "quarantine": "Non-injury",

}

dfInjuries['injury_category'] = (
    dfInjuries['Injury']
    .str.strip()
    .map(injury_map)
    .fillna("Other")
)
#unmapped = df[df['injury_category'] == "Other"]
#print(unmapped['Injury'].value_counts())


# 9. Bereinigte Daten speichern - Age Validation Merge Logic
# Füge eine temporäre ID hinzu, um Original-Verletzungen zu identifizieren
dfInjuries['temp_inj_id'] = range(len(dfInjuries))

# Führe einen Merge mit players durch, hole auch date_of_birth und player_id
df = pd.merge(
    dfInjuries, 
    dfPlayers[['name', 'player_id', 'market_value_in_eur', 'date_of_birth']], 
    left_on='player_name', 
    right_on='name', 
    how='left'
)

# Berechne das Geburtsjahr aus players.csv
df['player_birth_year'] = pd.to_datetime(df['date_of_birth'], errors='coerce').dt.year

# Berechne das Verletzungsjahr aus dem Datum
df['injury_year'] = pd.to_datetime(df['injury_from_parsed'], errors='coerce').dt.year

# Berechne das Geburtsjahr basierend auf dem Alter zum Zeitpunkt der Verletzung
# df['player_age'] kann leer/NaN sein, daher füllen wir NaN-Werte mit 0 oder nutzen floats
df['calculated_birth_year'] = df['injury_year'] - pd.to_numeric(df['player_age'], errors='coerce')

# Berechne die absolute Altersdifferenz
df['age_diff'] = (df['player_birth_year'] - df['calculated_birth_year']).abs()

# Sortiere nach der temporären Verletzungs-ID und der Altersdifferenz aufsteigend.
# So steht der Match mit der kleinsten Altersdifferenz ganz oben.
df = df.sort_values(by=['temp_inj_id', 'age_diff'])

# Behalte nur die erste Zeile für jede Original-Verletzung
df = df.drop_duplicates(subset=['temp_inj_id'], keep='first')

# 10. Vereinswechsel-Duplikate (Kategorie 2) auflösen
# Wir nutzen player_valuations, um den echten Verein zum Zeitpunkt der Verletzung zu finden
df['injury_from_parsed_dt'] = pd.to_datetime(df['injury_from_parsed'], errors='coerce')
df_sorted = df.sort_values('injury_from_parsed_dt').dropna(subset=['injury_from_parsed_dt'])

# Sicherstellen, dass player_id denselben Typ hat (int)
df_sorted['player_id'] = pd.to_numeric(df_sorted['player_id'], errors='coerce').fillna(-1).astype(int)
dfVals['player_id'] = pd.to_numeric(dfVals['player_id'], errors='coerce').fillna(-1).astype(int)

# Merge_asof benötigt sortierte DataFrames
# Dieser Merge holt uns den current_club_name, den der Spieler am nächsten am Verletzungsdatum hatte
df_resolved = pd.merge_asof(
    df_sorted, 
    dfVals[['player_id', 'date', 'current_club_name']].dropna(), 
    left_on='injury_from_parsed_dt', 
    right_on='date', 
    by='player_id', 
    direction='nearest'
)

# Funktion zur Bewertung, ob der Scraping-Club mit dem echten historischen Club übereinstimmt
def club_match(row):
    if pd.isna(row['current_club_name']) or pd.isna(row['club']):
        return 0
    c1 = str(row['club']).lower().replace(' ', '')
    c2 = str(row['current_club_name']).lower().replace(' ', '')
    if c1 in c2 or c2 in c1:
        return 1
    return 0

df_resolved['club_match_score'] = df_resolved.apply(club_match, axis=1)

# Definition eines echten Duplikats: Selber Spieler, selbe Verletzung, selbes Startdatum
subset_dup = ['player_name', 'Injury', 'injury_from_parsed']

# Wir sortieren nach den Duplikat-Spalten und absteigend nach unserem club_match_score.
# So steht die Zeile, bei der der Verein mit der Historie übereinstimmt, ganz oben.
df_resolved = df_resolved.sort_values(by=subset_dup + ['club_match_score'], ascending=[True, True, True, False])

# Jetzt löschen wir die Duplikate und behalten nur den echten Verein
df_final = df_resolved.drop_duplicates(subset=subset_dup, keep='first')

# Aufräumen der temporären Spalten
cols_to_drop = [
    'temp_inj_id', 'name', 'date_of_birth', 
    'player_birth_year', 'injury_year', 
    'calculated_birth_year', 'age_diff',
    'date', 'current_club_name', 'club_match_score', 'injury_from_parsed_dt'
]
df_final = df_final.drop(columns=[col for col in cols_to_drop if col in df_final.columns])

df_final.to_csv('./Data/cleaned_dataset_final.csv', index=False)

print("Bereinigung abgeschlossen. Datei gespeichert unter: cleaned_dataset_final.csv")

# Optional: Checks durchführen
#print(sorted(df['club'].unique()))
#print(sorted(df['player_name'].unique()))