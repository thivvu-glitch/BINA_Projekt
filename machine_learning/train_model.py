"""
Marktwert-Impact-Vorhersage bei Verletzungen (Training Script)

Dieses Skript entwickelt das Machine-Learning-Modell zur Vorhersage des prozentualen 
Marktwertverlusts eines Spielers nach einer Verletzung.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import joblib
import os
import warnings

from sklearn.model_selection import train_test_split, KFold, cross_validate
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

warnings.filterwarnings('ignore')

# Random State fixieren für Reproduzierbarkeit (Anforderung)
RANDOM_STATE = 42

def train_and_export_model():
    print("Starte ML-Training Pipeline...")

    # 1. Daten laden
    try:
        df_inj = pd.read_csv('Data/cleaned_dataset_final.csv')
        df_val = pd.read_csv('Data/player_valuations.csv')
    except FileNotFoundError as e:
        print(f"Fehler: Datei nicht gefunden. {e}")
        return

    # Datumsformate anpassen
    df_inj['injury_from_parsed'] = pd.to_datetime(df_inj['injury_from_parsed'])
    df_inj['injury_until_parsed'] = pd.to_datetime(df_inj['injury_until_parsed'])
    df_val['date'] = pd.to_datetime(df_val['date'])

    print(f"Verletzungen geladen: {len(df_inj)}")
    print(f"Marktwerte geladen: {len(df_val)}")

    # 2. Feature Engineering: Verletzungshistorie
    print("Berechne Feature Engineering (Historie & Marktwerte)...")
    df_inj = df_inj.sort_values(['player_id', 'injury_from_parsed']).reset_index(drop=True)
    df_val = df_val.sort_values(['player_id', 'date'])

    df_inj['previous_injuries_count'] = df_inj.groupby('player_id').cumcount()
    df_inj['Days_clean'] = df_inj['Days'].fillna(0)
    df_inj['total_previous_days_out'] = df_inj.groupby('player_id')['Days_clean'].transform(lambda x: x.shift().cumsum()).fillna(0)
    df_inj.drop(columns=['Days_clean'], inplace=True)

    # 3. Target Variable: Marktwertveränderung (delta_pct)
    mv_pre_list = []
    mv_post_list = []

    # Beschleunigte Iteration durch Gruppierung nach Spieler
    grouped_vals = df_val.groupby('player_id')

    for _, row in df_inj.iterrows():
        p_id = row['player_id']
        d_from = row['injury_from_parsed']
        d_until = row['injury_until_parsed']
        
        if pd.isna(d_from) or pd.isna(d_until) or p_id not in grouped_vals.groups:
            mv_pre_list.append(np.nan)
            mv_post_list.append(np.nan)
            continue
            
        p_vals = grouped_vals.get_group(p_id)
        
        # Marktwert VORHER
        pre_vals = p_vals[p_vals['date'] <= d_from]
        if pre_vals.empty:
            mv_pre_list.append(np.nan)
            mv_post_list.append(np.nan)
            continue
        mv_pre = pre_vals.iloc[-1]['market_value_in_eur']
        date_pre = pre_vals.iloc[-1]['date']
        
        # Marktwert NACHHER (Mindestabstand 30 Tage)
        post_vals = p_vals[p_vals['date'] >= d_until]
        mv_post = np.nan
        for _, post_row in post_vals.iterrows():
            if (post_row['date'] - date_pre).days >= 30:
                mv_post = post_row['market_value_in_eur']
                break
                
        mv_pre_list.append(mv_pre)
        mv_post_list.append(mv_post)

    df_inj['mv_pre'] = mv_pre_list
    df_inj['mv_post'] = mv_post_list
    df_inj['delta_pct'] = (df_inj['mv_post'] - df_inj['mv_pre']) / df_inj['mv_pre'] * 100

    # Datenbereinigung
    cols_to_check = ['delta_pct', 'mv_pre', 'player_age', 'player_position', 'league', 'injury_category', 'Days', 'Games missed', 'Season']
    df_ml = df_inj.dropna(subset=cols_to_check).copy()
    
    # Ausreisser filtern
    df_ml = df_ml[(df_ml['delta_pct'] >= -95) & (df_ml['delta_pct'] <= 200)]
    print(f"Samples nach Bereinigung und Filterung: {len(df_ml)}")

    # 4. Modellierung
    print("Trainiere Modelle...")
    numeric_features = ['player_age', 'Days', 'Games missed', 'mv_pre', 'previous_injuries_count', 'total_previous_days_out']
    categorical_features = ['player_position', 'injury_category', 'league', 'Season']

    X = df_ml[numeric_features + categorical_features]
    y = df_ml['delta_pct']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ])

    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE),
        'XGBoost': xgb.XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=RANDOM_STATE)
    }

    pipelines = {}
    for name, model in models.items():
        pipelines[name] = Pipeline([
            ('preprocessor', preprocessor),
            ('model', model)
        ])

    # Evaluation
    results = []
    kf = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    for name, pipeline in pipelines.items():
        # CV Score
        cv_scores = cross_validate(pipeline, X_train, y_train, cv=kf, scoring='r2')
        
        # Fit & Predict
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        results.append({
            'Model': name,
            'CV R²': cv_scores['test_score'].mean(),
            'Test R²': r2_score(y_test, y_pred),
            'Test MAE': mean_absolute_error(y_test, y_pred),
            'Test RMSE': np.sqrt(mean_squared_error(y_test, y_pred))
        })

    print("\n--- Model Evaluation Results ---")
    results_df = pd.DataFrame(results).round(4)
    print(results_df.to_string(index=False))
    print("--------------------------------\n")

    # 5. Export
    print("Berechne globale SHAP-Werte für Beeswarm-Plot...")
    xgb_model = pipelines['XGBoost'].named_steps['model']
    preprocessor = pipelines['XGBoost'].named_steps['preprocessor']
    
    X_sample = X_train.sample(min(500, len(X_train)), random_state=RANDOM_STATE)
    X_sample_transformed = preprocessor.transform(X_sample)
    cat_encoder = preprocessor.named_transformers_['cat']
    feature_names = numeric_features + list(cat_encoder.get_feature_names_out(categorical_features))
    
    explainer = shap.TreeExplainer(xgb_model)
    shap_values_global = explainer(pd.DataFrame(X_sample_transformed, columns=feature_names))

    print("Speichere Modell...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    export_data = {
        'model_pipeline': pipelines['XGBoost'],
        'baseline_pipeline': pipelines['Linear Regression'],
        'numeric_features': numeric_features,
        'categorical_features': categorical_features,
        'shap_values_global': shap_values_global
    }

    export_path = os.path.join(models_dir, 'mv_prediction_model.pkl')
    joblib.dump(export_data, export_path)
    print(f"✅ Modell-Export nach '{export_path}' erfolgreich.")

if __name__ == "__main__":
    train_and_export_model()
