import pandas as pd
import numpy as np
import xgboost as xgb
import warnings
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

warnings.filterwarnings('ignore')

RANDOM_STATE = 42

def prepare_data():
    """Lädt und bereitet die Daten genauso vor wie im Training-Skript."""
    print("Lade und bereite Daten für die Evaluierung vor...")
    try:
        df_inj = pd.read_csv('Data/cleaned_dataset_final.csv')
        df_val = pd.read_csv('Data/player_valuations.csv')
    except FileNotFoundError as e:
        print(f"Fehler: Datei nicht gefunden. Bitte stelle sicher, dass du im Stammverzeichnis bist. {e}")
        return None, None

    df_inj['injury_from_parsed'] = pd.to_datetime(df_inj['injury_from_parsed'])
    df_inj['injury_until_parsed'] = pd.to_datetime(df_inj['injury_until_parsed'])
    df_val['date'] = pd.to_datetime(df_val['date'])

    df_inj = df_inj.sort_values(['player_id', 'injury_from_parsed']).reset_index(drop=True)
    df_val = df_val.sort_values(['player_id', 'date'])

    df_inj['previous_injuries_count'] = df_inj.groupby('player_id').cumcount()
    df_inj['Days_clean'] = df_inj['Days'].fillna(0)
    df_inj['total_previous_days_out'] = df_inj.groupby('player_id')['Days_clean'].transform(lambda x: x.shift().cumsum()).fillna(0)
    df_inj.drop(columns=['Days_clean'], inplace=True)

    mv_pre_list = []
    mv_post_list = []
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
        
        pre_vals = p_vals[p_vals['date'] <= d_from]
        if pre_vals.empty:
            mv_pre_list.append(np.nan)
            mv_post_list.append(np.nan)
            continue
        mv_pre = pre_vals.iloc[-1]['market_value_in_eur']
        date_pre = pre_vals.iloc[-1]['date']
        
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

    cols_to_check = ['delta_pct', 'mv_pre', 'player_age', 'player_position', 'league', 'injury_category', 'Days', 'Games missed', 'Season']
    df_ml = df_inj.dropna(subset=cols_to_check).copy()
    df_ml = df_ml[(df_ml['delta_pct'] >= -95) & (df_ml['delta_pct'] <= 200)]

    numeric_features = ['player_age', 'Days', 'Games missed', 'mv_pre', 'previous_injuries_count', 'total_previous_days_out']
    categorical_features = ['player_position', 'injury_category', 'league', 'Season']

    X = df_ml[numeric_features + categorical_features]
    y = df_ml['delta_pct']

    return X, y, numeric_features, categorical_features

def evaluate_models():
    X, y, numeric_features, categorical_features = prepare_data()
    if X is None:
        return

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

    print("\n" + "="*60)
    print("TEST MODELL WERTE & EVALUIERUNG".center(60))
    print("="*60)

    for name, pipeline in pipelines.items():
        # Trainiere Modell
        pipeline.fit(X_train, y_train)
        
        # Vorhersagen auf Train- und Test-Set
        y_train_pred = pipeline.predict(X_train)
        y_test_pred = pipeline.predict(X_test)
        
        # Metriken berechnen
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

        r2_diff = train_r2 - test_r2

        print(f"\nModell: {name}")
        print("-" * 40)
        print(f"R² Score:   Train = {train_r2:.4f} | Test = {test_r2:.4f} | Diff = {r2_diff:.4f}")
        print(f"MAE:        Train = {train_mae:.4f} | Test = {test_mae:.4f}")
        print(f"RMSE:       Train = {train_rmse:.4f} | Test = {test_rmse:.4f}")

if __name__ == "__main__":
    evaluate_models()
