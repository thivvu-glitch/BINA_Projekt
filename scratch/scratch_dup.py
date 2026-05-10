import pandas as pd

df = pd.read_csv('./Data/full_dataset_thesis - 1.csv', encoding='utf-8')
print(f"Original injuries: {len(df)}")
dupes = df[df.duplicated(keep=False)]
print(f"Exact duplicates in original data: {len(dupes)}")

# test duplicates like Test_duplicate.py on original data
subset_no_club = [col for col in df.columns if col not in ['club', 'league']]
dupes_no_club = df[df.duplicated(subset=subset_no_club, keep=False)]
transfers_only = dupes_no_club[~dupes_no_club.index.isin(dupes.index)]
print(f"Transfer duplicates in original data: {len(transfers_only)}")

subset_start = ['player_name', 'Injury', 'injury_from_parsed']
dupes_start = df[df.duplicated(subset=subset_start, keep=False)]
diff_duration = dupes_start[~dupes_start.index.isin(dupes.index) & ~dupes_start.index.isin(transfers_only.index)]
print(f"Category 3 in original data: {len(diff_duration)}")
