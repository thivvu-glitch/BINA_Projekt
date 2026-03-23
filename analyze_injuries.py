import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# Set aesthetic style
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['figure.figsize'] = (12, 6)

# Path to dataset
dataset_path = "/Users/thivvirthan/.cache/kagglehub/datasets/sananmuzaffarov/european-football-injuries-2020-2025/versions/2/full_dataset_thesis - 1.csv"
output_dir = "/Users/thivvirthan/.gemini/antigravity/brain/909000be-27a1-4920-a514-d1c779859a22/"

# Step 2: Identify and Prepare Data
print("Loading data...")
df = pd.read_csv(dataset_path)

# Cleaning 'Days' column
df['Days'] = df['Days'].str.replace(' days', '').str.replace('-', '0').fillna('0')
df['Days'] = pd.to_numeric(df['Days'], errors='coerce').fillna(0).astype(int)

# Cleaning 'Games missed'
df['Games missed'] = pd.to_numeric(df['Games missed'], errors='coerce').fillna(0).astype(int)

# Parsing Dates
df['injury_from_parsed'] = pd.to_datetime(df['injury_from_parsed'], errors='coerce')
df['Month'] = df['injury_from_parsed'].dt.month_name()
df['Month_Num'] = df['injury_from_parsed'].dt.month

# Step 3: Explore and Analyze Data

# 1. League with highest injury frequency
print("Analyzing injury frequency per league...")
league_freq = df['league'].value_counts().reset_index()
league_freq.columns = ['League', 'Count']

plt.figure()
sns.barplot(data=league_freq, x='Count', y='League')
plt.title('Injury Frequency per League (2020-2025)')
plt.xlabel('Number of Injuries')
plt.savefig(os.path.join(output_dir, 'injury_frequency_league.png'))
plt.close()

# 2. Most severe injuries (Days missed) per league
print("Analyzing injury severity...")
league_severity = df.groupby('league')['Days'].mean().sort_values(ascending=False).reset_index()

plt.figure()
sns.barplot(data=league_severity, x='Days', y='league')
plt.title('Average Days Missed per Injury by League')
plt.xlabel('Average Days Out')
plt.savefig(os.path.join(output_dir, 'injury_severity_league.png'))
plt.close()

# 3. Seasonal Patterns (Monthly)
print("Analyzing seasonal patterns...")
monthly_trends = df.groupby(['Month_Num', 'Month']).size().reset_index(name='Count').sort_values('Month_Num')

plt.figure()
sns.lineplot(data=monthly_trends, x='Month', y='Count', marker='o')
plt.title('Monthly Injury Distribution (Combined Seasons)')
plt.xticks(rotation=45)
plt.ylabel('Injury Count')
plt.savefig(os.path.join(output_dir, 'seasonal_trends.png'))
plt.close()

# 4. Top "Pechvögel" (Players with highest cumulative days missed)
print("Identifying top injured players...")
top_players = df.groupby('player_name')['Days'].sum().sort_values(ascending=False).head(10).reset_index()

plt.figure()
sns.barplot(data=top_players, x='Days', y='player_name')
plt.title('Top 10 Players by Cumulative Days Missed (2020-2025)')
plt.xlabel('Total Days Out')
plt.savefig(os.path.join(output_dir, 'top_players_out.png'))
plt.close()

print("Analysis complete. Visualizations saved to artifact directory.")

# Summary statistics for Step 4
print("\n--- Summary Statistics ---")
print(f"Total Injuries: {len(df)}")
print(f"Total Days Missed: {df['Days'].sum()}")
print(f"Average Days per Injury: {df['Days'].mean():.2f}")
print("\nLeague with most injuries:", league_freq.iloc[0]['League'])
print("League with highest average severity:", league_severity.iloc[0]['league'])
print("Top unlucky player:", top_players.iloc[0]['player_name'], f"({top_players.iloc[0]['Days']} days)")
