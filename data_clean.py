import pandas as pd

# 1. Daten laden
df = pd.read_csv('./Data/full_dataset_thesis - 1.csv')

# 2. Bereinigung der 'Days'-Spalte (z. B. "10 days" -> 10, "-" -> 0)
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
    'Roma': 'AS Roma',
    'Verona': 'Hellas Verona',
}
df['club'] = df['club'].replace(club_mapping)

# 6. Verletzungen vereinheitlichen (Kleinschreibung)
df['Injury'] = df['Injury'].str.lower()

# 8. Kategorisierung der Verletzungen
injury_map = {

    # ---------------- MUSCLE ----------------
    "torn muscle fiber": "Muscle",
    "torn muscle bundle": "Muscle",
    "muscle injury": "Muscle",
    "muscular problems": "Muscle",
    "hamstring injury": "Muscle",
    "hamstring strain": "Muscle",
    "hamstring muscle injury": "Muscle",
    "muscle strain": "Muscle",
    "muscle tear": "Muscle",
    "partial muscle tear": "Muscle",
    "torn thigh muscle": "Muscle",
    "muscle contusion": "Muscle",
    "calf injury": "Muscle",
    "calf strain": "Muscle",
    "calf muscle tear": "Muscle",
    "calf problems": "Muscle",
    "adductor pain": "Muscle",
    "adductor injury": "Muscle",
    "adductor strain": "Muscle",
    "thigh problems": "Muscle",
    "dead leg": "Muscle",
    "muscle stiffness": "Muscle",
    "muscle fatigue": "Muscle",
    "sore muscles": "Muscle",
    "leg injury": "Muscle",
    "strain": "Muscle",


    # ---------------- LIGAMENT / TENDON ----------------
    "ligament injury": "Ligament",
    "ligament tear": "Ligament",
    "torn ligaments": "Ligament",
    "cruciate ligament tear": "Ligament",
    "cruciate ligament injury": "Ligament",
    "cruciate ligament strain": "Ligament",
    "inner ligament injury": "Ligament",
    "inner ligament tear": "Ligament",
    "collateral ligament tear": "Ligament",
    "collateral ligament injury": "Ligament",
    "ankle ligament tear": "Ligament",
    "torn ankle ligaments": "Ligament",
    "syndesmosis ligament tear": "Ligament",
    "syndesmotic ligament tear": "Ligament",
    "ligament stretching": "Ligament",
    "groin injury": "Ligament",
    "groin problems": "Ligament",
    "achilles tendon injury": "Ligament",
    "pubalgia": "Ligament",
    "achilles tendon problems": "Ligament",
    "achilles tendon rupture": "Ligament",

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

    # ---------------- ANKLE / FOOT ----------------
    "ankle injury": "Ankle/Foot",
    "ankle problems": "Ankle/Foot",
    "ankle sprain": "Ankle/Foot",
    "foot injury": "Ankle/Foot",
    "metatarsal fracture": "Ankle/Foot",
    "broken toe": "Ankle/Foot",
    "toe injury": "Ankle/Foot",
    "heel problems": "Ankle/Foot",
    "heel injury": "Ankle/Foot",
    "injury to the ankle": "Ankle/Foot",

    # ---------------- BONE / FRACTURE ----------------
    "broken fibula": "Fracture",
    "broken ankle": "Fracture",
    "broken arm": "Fracture",
    "broken hand": "Fracture",
    "broken finger": "Fracture",
    "broken leg": "Fracture",
    "broken foot": "Fracture",
    "rib fracture": "Fracture",
    "skull fracture": "Fracture",
    "forearm fracture": "Fracture",
    "lumbar vertebra fracture": "Fracture",
    "fracture": "Fracture",
    "hairline crack in foot": "Fracture",
    "fatigue fracture": "Fracture",
    "hip injury": "Fracture",
    "hip problems": "Fracture",

    # ---------------- BACK / SPINE ----------------
    "back problems": "Back/Spine",
    "back injury": "Back/Spine",
    "herniated disc": "Back/Spine",
    "lumbago": "Back/Spine",
    "cervical spine injury": "Back/Spine",
    "compression of the spine": "Back/Spine",

    # ---------------- ILLNESS / VIRUS ----------------
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

    # ---------------- HEAD ----------------
    "concussion": "Head",
    "head injury": "Head",
    "eye injury": "Head",
    "facial injury": "Head",
    "broken nose bone": "Head",

    # ---------------- SHOULDER ----------------
    "shoulder injury": "Shoulder",
    "shoulder problems": "Shoulder",

    # ---------------- SURGERY ----------------
    "surgery": "Surgery",
    "ankle surgery": "Surgery",
    "foot surgery": "Surgery",
    "dental surgery": "Surgery",
    "arthroscopy": "Surgery",
    "groin surgery": "Surgery",

    # ---------------- NON-INJURY ----------------
    "fitness": "Non-injury",
    "rest": "Non-injury",
    "quarantine": "Non-injury",

    # ---------------- MINOR ----------------
    "minor knock": "Minor",
    "knock": "Minor",
    "bruise": "Minor",
    "bruised ribs": "Minor",
    "bone bruise": "Minor",
    "inflammation of pubic bone": "Minor",
    "inflammation": "Minor",
    "stomach problems": "Minor",
    "hand injury": "Minor",

}

df['injury_category'] = (
    df['Injury']
    .str.strip()
    .map(injury_map)
    .fillna("Other")
)
#unmapped = df[df['injury_category'] == "Other"]
#print(unmapped['Injury'].value_counts())


# 9. Bereinigte Daten speichern
df.to_csv('./Data/cleaned_dataset_final.csv', index=False)

print("Bereinigung abgeschlossen. Datei gespeichert unter: cleaned_dataset_final.csv")

# Optional: Checks durchführen
#print(sorted(df['club'].unique()))
#print(sorted(df['player_name'].unique()))