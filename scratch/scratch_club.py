import pandas as pd

val = pd.read_csv('./Data/player_valuations.csv')
pl = pd.read_csv('./Data/players.csv')
val['date'] = pd.to_datetime(val['date'])
val = val.sort_values('date')

inj = pd.DataFrame({
    'name': ['Aaron Ramsdale', 'Abdou Diallo'],
    'injury_date': pd.to_datetime(['2025-01-24', '2023-01-23'])
})
inj = pd.merge(inj, pl[['name', 'player_id']], on='name')
inj = inj.sort_values('injury_date')

result = pd.merge_asof(inj, val[['player_id', 'date', 'current_club_name']].dropna(), 
                       left_on='injury_date', right_on='date', by='player_id', direction='nearest')

print(result)
