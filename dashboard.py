import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import os

# Page Config
st.set_page_config(page_title="Europäische Fussballverletzungen Dashboard", layout="wide")

# Title and Description
st.title("⚽ Europäische Fussballverletzungen (2020-2025)")
st.markdown("""
Dieses Dashboard ermöglicht die Analyse von Verletzungsmustern im europäischen Profifussball.
Basiert auf der **CPA Management Accounting Guideline** für datengesteuerte Entscheidungen.
""")

# Load Data
@st.cache_data
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(script_dir, "full_dataset_thesis - 1.csv")
    df = pd.read_csv(path, encoding='utf8')
    # Cleaning 'Days'
    df['Days'] = df['Days'].str.replace(' days', '').str.replace('-', '0').fillna('0')
    df['Days'] = pd.to_numeric(df['Days'], errors='coerce').fillna(0).astype(int)
    # Cleaning 'Games missed'
    df['Games missed'] = pd.to_numeric(df['Games missed'], errors='coerce').fillna(0).astype(int)
    # Dates
    df['injury_from_parsed'] = pd.to_datetime(df['injury_from_parsed'], errors='coerce')
    df['Month'] = df['injury_from_parsed'].dt.month_name()
    df['Month_Num'] = df['injury_from_parsed'].dt.month
    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("Filteroptionen")

# League Filter
leagues = sorted(df['league'].unique().tolist())
selected_leagues = st.sidebar.multiselect("Ligen auswählen", leagues, default=leagues)

# Season Filter
seasons = sorted(df['Season'].unique().tolist())
selected_seasons = st.sidebar.multiselect("Saisons auswählen", seasons, default=seasons)

# Player Search
player_search = st.sidebar.text_input("Spieler suchen (z.B. Sasa Kalajdzic)")

# Filter Data
filtered_df = df[
    (df['league'].isin(selected_leagues)) &
    (df['Season'].isin(selected_seasons))
]

if player_search:
    filtered_df = filtered_df[filtered_df['player_name'].str.contains(player_search, case=False, na=False)]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Gesamtverletzungen", f"{len(filtered_df):,}".replace(",", "."))
col2.metric("Ausfalltage insgesamt", f"{filtered_df['Days'].sum():,}".replace(",", "."))
col3.metric("Ø Tage pro Verletzung", f"{filtered_df['Days'].mean():.1f}".replace(".", ",") if len(filtered_df) > 0 else "0")
col4.metric("Ø Verpasste Spiele", f"{filtered_df['Games missed'].mean():.1f}".replace(".", ",") if len(filtered_df) > 0 else "0")

# Charts
st.divider()

c1, c2 = st.columns(2)

with c1:
    st.subheader("Verletzungshäufigkeit nach Liga")
    league_counts = filtered_df['league'].value_counts().reset_index()
    league_counts.columns = ['Liga', 'Verletzungen']
    fig_league = px.bar(league_counts, x='Verletzungen', y='Liga', orientation='h', 
                        color='Verletzungen', color_continuous_scale='Reds')
    st.plotly_chart(fig_league, use_container_width=True)

with c2:
    st.subheader("Schweregrad nach Liga (Ø Tage)")
    severity = filtered_df.groupby('league')['Days'].mean().sort_values(ascending=False).reset_index()
    fig_sev = px.bar(severity, x='Days', y='league', orientation='h',
                     labels={'Days': 'Ø Ausfalltage', 'league': 'Liga'}, color='Days', color_continuous_scale='Blues')
    st.plotly_chart(fig_sev, use_container_width=True)

st.divider()

c3, c4 = st.columns(2)

with c3:
    st.subheader("Saisonale Muster im Ligenvergleich")
    monthly = filtered_df.groupby(['Month_Num', 'Month', 'league']).size().reset_index(name='Anzahl').sort_values('Month_Num')
    fig_month = px.line(monthly, x='Month', y='Anzahl', color='league', markers=True, 
                        title="Verletzungen im Jahresverlauf nach Ligen",
                        labels={'Month': 'Monat', 'Anzahl': 'Anzahl Verletzungen', 'league': 'Liga'})
    st.plotly_chart(fig_month, use_container_width=True)

with c4:
    st.subheader("Top 'Pechvögel' (Längste Ausfallzeiten)")
    top_p = filtered_df.groupby('player_name')['Days'].sum().sort_values(ascending=False).head(15).reset_index()
    fig_top = px.bar(top_p, x='Days', y='player_name', orientation='h',
                     color='Days', color_continuous_scale='Viridis',
                     labels={'Days': 'Ausfalltage', 'player_name': 'Spieler'})
    st.plotly_chart(fig_top, use_container_width=True)

# Saisonvergleich Graphik
st.divider()
st.subheader("Verletzungsentwicklung über die Saisons")
season_counts = filtered_df.groupby(['Season', 'league']).size().reset_index(name='Anzahl')
if not season_counts.empty:
    fig_season = px.bar(season_counts, x='Season', y='Anzahl', color='league', barmode='group',
                        labels={'Season': 'Saison', 'Anzahl': 'Anzahl Verletzungen', 'league': 'Liga'})
    st.plotly_chart(fig_season, use_container_width=True)
else:
    st.write("Keine Daten für diesen Vergleich verfügbar.")

# Automatisches Fazit
st.divider()
st.subheader("Automatisches Fazit zum Ligenvergleich")
if len(selected_leagues) >= 2 and not filtered_df.empty:
    most_injuries_league = filtered_df['league'].value_counts().idxmax()
    most_severe_league = filtered_df.groupby('league')['Days'].mean().idxmax()
    
    monthly_peak = filtered_df.groupby(['league', 'Month'])['Days'].count().reset_index()
    monthly_peak.columns = ['league', 'Month', 'Count']
    monthly_peak = monthly_peak.loc[monthly_peak.groupby('league')['Count'].idxmax()]
    
    fazit_text = f"**Vergleich der ausgewählten Ligen ({', '.join(selected_leagues)}):**\n\n"
    fazit_text += f"- **Häufigkeit:** Die absolute Mehrheit der Verletzungen weist die **{most_injuries_league}** auf.\n"
    fazit_text += f"- **Schweregrad:** Die längsten durchschnittlichen Ausfallzeiten gibt es in der **{most_severe_league}**.\n"
    fazit_text += "- **Saisonale Spitzen (Wann steigen die Verletzungen?):**\n"
    
    for _, row in monthly_peak.iterrows():
        fazit_text += f"  - In der **{row['league']}** gibt es den höchsten Anstieg an Verletzungen im **{row['Month']}**.\n"
        
    st.info(fazit_text)
elif len(selected_leagues) < 2:
    st.info("Wähle in der Seitenleiste mindestens zwei Ligen aus, um ein automatisches Vergleichs-Fazit zu generieren.")
else:
    st.info("Keine Daten für ein Fazit vorhanden.")

# Data Tables
st.divider()
st.subheader("Detaillierte Tabellenansicht")

# Toggle for comparison mode
comparison_mode = st.radio(
    "Tabellen gruppieren nach:",
    options=["Liga", "Saison"],
    horizontal=True
)

if comparison_mode == "Liga":
    if not selected_leagues:
        st.info("Bitte wähle mindestens eine Liga aus, um die Tabellen zu sehen.")
    else:
        for league in selected_leagues:
            st.markdown(f"### {league}")
            league_df = filtered_df[filtered_df['league'] == league]
            
            if league_df.empty:
                st.write("Keine Daten für die aktuellen Filter in dieser Liga.")
            else:
                # Reorder and rename columns for display
                display_df = league_df[['Season', 'player_name', 'club', 'Injury', 'Days', 'Games missed']].copy()
                display_df.columns = ['Saison', 'Spieler', 'Verein', 'Verletzung', 'Ausfalltage', 'Verpasste Spiele']
                display_df = display_df.sort_values('Ausfalltage', ascending=False)
                st.dataframe(display_df, use_container_width=True, hide_index=True)

elif comparison_mode == "Saison":
    if not selected_seasons:
        st.info("Bitte wähle mindestens eine Saison aus, um die Tabellen zu sehen.")
    else:
        for season in selected_seasons:
            st.markdown(f"### Saison {season}")
            season_df = filtered_df[filtered_df['Season'] == season]
            
            if season_df.empty:
                st.write("Keine Daten für die aktuellen Filter in dieser Saison.")
            else:
                # Reorder and rename columns for display
                display_df = season_df[['league', 'player_name', 'club', 'Injury', 'Days', 'Games missed']].copy()
                display_df.columns = ['Liga', 'Spieler', 'Verein', 'Verletzung', 'Ausfalltage', 'Verpasste Spiele']
                display_df = display_df.sort_values('Ausfalltage', ascending=False)
                st.dataframe(display_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Entwickelt für Senior Data Scientist Analyse (CPA Framework).")
