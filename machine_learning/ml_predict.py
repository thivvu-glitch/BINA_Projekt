import joblib
import pandas as pd
import numpy as np
import shap
import os

# Pfad zum Modell-Ordner
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models/mv_prediction_model.pkl')

def load_ml_model():
    """Lädt das vortrainierte XGBoost-Modell und die Feature-Struktur."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Modell-Datei nicht gefunden unter: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)

def predict_market_change(age: int, position: str, injury_category: str, days_out: int, 
                          current_mv: float, league: str, prev_injuries: int, 
                          total_prev_days: int) -> dict:
    """
    Führt eine Vorhersage des Marktwert-Drops für einen gegebenen Spieler durch.
    
    Args:
        age (int): Alter des Spielers.
        position (str): Spielposition.
        injury_category (str): Kategorie der Verletzung.
        days_out (int): Erwartete Ausfalltage.
        current_mv (float): Aktueller Marktwert in EUR.
        league (str): Aktuelle Liga.
        prev_injuries (int): Anzahl bisheriger Verletzungen.
        total_prev_days (int): Anzahl kumulierter bisheriger Ausfalltage.
        
    Returns:
        dict: Ein Dictionary mit den Vorhersageergebnissen und SHAP-Daten.
    """
    model_data = load_ml_model()
    pipeline = model_data['model_pipeline']
    
    # Saison wird standardmässig auf die aktuelle gesetzt, falls das Modell sie erfordert
    # (Dies war in den kategorischen Features als 'Season' definiert)
    current_season = '24/25'
    
    # 1. Eingabedaten als DataFrame formatieren
    input_data = pd.DataFrame([{
        'player_age': age,
        'Days': days_out,
        'Games missed': max(0, int(days_out / 7)), # Annahme: 1 Spiel pro Woche
        'mv_pre': current_mv,
        'previous_injuries_count': prev_injuries,
        'total_previous_days_out': total_prev_days,
        'player_position': position,
        'injury_category': injury_category,
        'league': league,
        'Season': current_season
    }])
    
    # 2. Vorhersage durchführen
    predicted_delta_pct = pipeline.predict(input_data)[0]
    
    # Sicherstellen, dass das Delta nicht positiv wird (falls das Modell leicht drüber ist)
    # Ein Marktwert-Zuwachs durch Verletzung ist unlogisch.
    if predicted_delta_pct > 0:
        predicted_delta_pct = 0.0
        
    # Monetären Verlust berechnen
    predicted_loss_eur = (predicted_delta_pct / 100) * current_mv
    new_market_value = current_mv + predicted_loss_eur
    
    # 3. SHAP-Werte für die Erklärbarkeit berechnen
    # Das XGBoost Modell aus der Pipeline holen
    xgb_model = pipeline.named_steps['model']
    preprocessor = pipeline.named_steps['preprocessor']
    
    # Input transformieren
    input_transformed = preprocessor.transform(input_data)
    
    # Feature Names rekonstruieren
    cat_features = model_data['categorical_features']
    num_features = model_data['numeric_features']
    cat_encoder = preprocessor.named_transformers_['cat']
    feature_names = num_features + list(cat_encoder.get_feature_names_out(cat_features))
    
    # SHAP Explainer
    explainer = shap.TreeExplainer(xgb_model)
    shap_values = explainer(pd.DataFrame(input_transformed, columns=feature_names))
    
    return {
        'drop_pct': predicted_delta_pct,
        'loss_eur': predicted_loss_eur,
        'new_mv': new_market_value,
        'shap_values': shap_values,
        'feature_names': feature_names,
        'input_transformed': input_transformed
    }
