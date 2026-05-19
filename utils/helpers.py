import streamlit as st
import pandas as pd

def get_injury_color(category, injury_name):
    cat = str(category).lower()
    inj = str(injury_name).lower()
    
    # Rot (Trauma/Struktur)
    if any(x in cat for x in ['knee', 'ankle', 'foot', 'shoulder']) or \
       any(x in inj for x in ['fracture', 'torn', 'break', 'rupture', 'ligament']):
        return "red"
    
    # Orange (Muskulär)
    if 'muscle' in cat or any(x in inj for x in ['hamstring', 'adductor', 'muscle', 'fibers', 'strain']):
        return "orange"
        
    # Gelb (Krankheit)
    if 'illness' in cat or any(x in inj for x in ['illness', 'internal', 'cold', 'flu', 'infection']):
        return "yellow"
        
    # Grau (Andere)
    return "grey"

@st.cache_data
def build_player_options(source_df, players_info_subset):
    """Erstellt eine Mapping-Tabelle: Anzeige-Label -> player_id"""
    unique_players = (source_df.dropna(subset=['player_id'])
                              .groupby('player_id')
                              .agg(name=('player_name', 'first'))
                              .reset_index())
    
    # Doppelte Namen erkennen und mit Geburtsjahr disambiguieren
    name_counts = unique_players['name'].value_counts()
    duplicate_names = name_counts[name_counts > 1].index
    
    # Geburtsjahr aus players_info_subset holen für Duplikate
    options = {}
    for _, row in unique_players.iterrows():
        p_id = int(row['player_id'])
        if row['name'] in duplicate_names:
            birth = players_info_subset.loc[players_info_subset['player_id'] == p_id, 'date_of_birth']
            year = pd.to_datetime(birth.iloc[0]).year if not birth.empty and pd.notna(birth.iloc[0]) else "?"
            label = f"{row['name']} (*{year})"
        else:
            label = row['name']
        options[label] = p_id
    
    return options

def calculate_contract_risk(player_data, market_value):
    """
    Berechnet Risiko-Metriken für Vertragsanalyse basierend auf durchschnittlichen Ausfalltagen
    
    Args:
        player_data: DataFrame mit Verletzungsdaten des Spielers
        market_value: Aktueller Marktwert in EUR
    
    Returns:
        dict mit Risiko-Metriken und Empfehlungen
    """
    if player_data.empty or pd.isna(market_value) or market_value == 0:
        return None
    
    total_days = player_data['Days'].sum()
    total_injuries = len(player_data)
    seasons_active = player_data['Season'].nunique()
    
    # Berechne durchschnittliche Ausfalltage pro Verletzung (Basis für Risikoklassifizierung)
    avg_days_per_injury = total_days / total_injuries if total_injuries > 0 else 0
    
    # Finanzielle Berechnungen
    career_years = 5
    daily_opportunity_cost = market_value / (career_years * 365)
    financial_impact = daily_opportunity_cost * total_days
    risk_percentage = (total_days / (career_years * 365)) * 100
    annual_impact = (total_days / max(seasons_active, 1)) * daily_opportunity_cost
    
    # Risiko-Level bestimmen basierend auf durchschnittlichen Ausfalltagen pro Verletzung
    if avg_days_per_injury > 60:
        risk_level = "🔴 Hohes Risiko"
        risk_color = "red"
        contract_action = f"""
        **Vertrag mit Vorsicht abschließen:**
        - Pay-per-Play oder leistungsbezogene Bonusstruktur erwägen
        - Kurze Bindungsfrist (max. 2 Jahre)
        - Versicherung/Absicherungsklauseln prüfen
        - Engere medizinische Betreuung kalkulieren
        - **Grund:** Ø {avg_days_per_injury:.1f} Tage pro Verletzung (hohe Schweregrad)
        """
    elif avg_days_per_injury > 30:
        risk_level = "🟡 Moderates Risiko"
        risk_color = "orange"
        contract_action = f"""
        **Standardvertrag mit Abstimmung:**
        - Normale Laufzeit (3-4 Jahre)
        - Leichte Performance-Bonuskomponente
        - Regelmäßige medizinische Checkups
        - **Grund:** Ø {avg_days_per_injury:.1f} Tage pro Verletzung (mittlere Schweregrad)
        """
    else:
        risk_level = "🟢 Geringes Risiko"
        risk_color = "green"
        contract_action = f"""
        **Unbedenkliche Vertragsverlängerung:**
        - Standard-Konditionen möglich
        - Stabilerer Asset-Value
        - Normale Belastungsplanung
        - **Grund:** Ø {avg_days_per_injury:.1f} Tage pro Verletzung (geringe Schweregrad)
        """
    
    return {
        "risk_level": risk_level,
        "risk_color": risk_color,
        "total_days": total_days,
        "total_injuries": total_injuries,
        "financial_impact": financial_impact,
        "risk_percentage": risk_percentage,
        "avg_days_per_injury": avg_days_per_injury,
        "annual_impact": annual_impact,
        "contract_action": contract_action
    }
