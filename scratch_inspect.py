import pandas as pd
import os

script_dir = "/Users/thivvirthan/Desktop/Verletzunganalyse/pages"
val_path = os.path.join(script_dir, "../Data/player_valuations.csv")
players_path = os.path.join(script_dir, "../Data/players.csv")

val_df = pd.read_csv(val_path)
players_df = pd.read_csv(players_path)

print("val_df columns:", val_df.columns.tolist())
print("players_df columns:", players_df.columns.tolist())
