import pandas as pd

# 1. Daten laden
file_path = './Data/cleaned_dataset_final.csv'
print(f"Lade Datensatz von: {file_path}...\n")
df = pd.read_csv(file_path, encoding='utf-8')

# Leichte Bereinigung für den Textvergleich
for col in ['Injury', 'player_name', 'club']:
    df[col] = df[col].astype(str).str.strip()
df['Injury'] = df['Injury'].str.lower()

# Sicherstellen, dass 'Days' als Zahl verglichen wird
df['Days'] = df['Days'].astype(str).str.replace(' days', '').str.replace('-', '0').fillna('0')
df['Days'] = pd.to_numeric(df['Days'], errors='coerce').fillna(0).astype(int)

cols_to_show = ['player_name', 'Injury', 'injury_from_parsed', 'Days', 'club']

print("Suche nach ALLEN Arten von Duplikaten im Datenset...\n")

# --- KATEGORIE 1: 100% EXAKTE DUPLIKATE (Identisch in wirklich ALLEN Spalten) ---
# Das sind Zeilen, die völlig identisch kopiert wurden (auch gleicher Verein).
exact_all_cols = df[df.duplicated(keep=False)].sort_values(by=['player_name', 'injury_from_parsed'])

print("=== KATEGORIE 1: 100% IDENTISCHE ZEILEN ===")
print("Hier ist wirklich jede einzelne Spalte (auch Verein, Liga, Tage) exakt gleich.")
print(f"Anzahl: {len(exact_all_cols)} Zeilen")
if len(exact_all_cols) > 0:
    print(exact_all_cols[cols_to_show].head(6).to_string(index=False))
print("\n" + "="*60 + "\n")


# --- KATEGORIE 2: VEREINSWECHSEL-DUPLIKATE (Alles gleich, aber unterschiedlicher Verein) ---
# Wir suchen Einträge, wo alle Daten gleich sind, aber der Club oder die Liga unterschiedlich ist.
subset_no_club = [col for col in df.columns if col not in ['club', 'league']]
dupes_no_club = df[df.duplicated(subset=subset_no_club, keep=False)]

# Schließe die 100% identischen Zeilen aus, damit wir hier NUR die Vereinswechsel sehen
transfers_only = dupes_no_club[~dupes_no_club.index.isin(exact_all_cols.index)].sort_values(by=['player_name', 'injury_from_parsed'])

print("=== KATEGORIE 2: VEREINSWECHSEL-DUPLIKATE ===")
print("Gleiche Verletzung, gleiches Datum, gleiche Dauer, ABER bei ZWEI VERSCHIEDENEN CLUBS.")
print(f"Anzahl: {len(transfers_only)} Zeilen")
if len(transfers_only) > 0:
    print(transfers_only[cols_to_show].head(6).to_string(index=False))
print("\n" + "="*60 + "\n")


# --- KATEGORIE 3: FEHLERHAFTE DOPPELEINTRÄGE (Gleiches Startdatum, unterschiedliche Dauer) ---
# Wir suchen Einträge mit gleichem Spieler, Verletzung und Startdatum...
subset_start = ['player_name', 'Injury', 'injury_from_parsed']
dupes_start = df[df.duplicated(subset=subset_start, keep=False)]

# ...die aber nicht in Kat 1 oder Kat 2 fallen (weil z.B. die Dauer abweicht)
diff_duration = dupes_start[~dupes_start.index.isin(exact_all_cols.index) & ~dupes_start.index.isin(transfers_only.index)].sort_values(by=['player_name', 'injury_from_parsed'])

print("=== KATEGORIE 3: FEHLERHAFTE DOPPELEINTRÄGE (Unterschiedliche Dauer) ===")
print("Ein Spieler hat am SELBEN Tag dieselbe Verletzung, aber mit UNTERSCHIEDLICHEN Ausfalltagen.")
print(f"Anzahl: {len(diff_duration)} Zeilen")
if len(diff_duration) > 0:
    print(diff_duration[cols_to_show].head(8).to_string(index=False))
print("\n" + "="*60 + "\n")


# --- CSV-EXPORT ---
exact_all_cols.to_csv('1_Volle_Duplikate.csv', index=False)
transfers_only.to_csv('2_Vereinswechsel_Duplikate.csv', index=False)
diff_duration.to_csv('3_Unterschiedliche_Dauer_Duplikate.csv', index=False)

print("Ich habe drei CSV-Dateien exportiert ('1_Volle_Duplikate.csv', '2_...', '3_...').")
print("Damit kannst du dir in Excel genau anschauen, um welche Art von Duplikat es sich handelt!")
