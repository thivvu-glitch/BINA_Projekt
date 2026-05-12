import json

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Marktwert-Impact-Vorhersage bei Verletzungen\n",
                "\n",
                "Dieses Notebook entwickelt das Machine-Learning-Modell zur Vorhersage des prozentualen Marktwertverlusts eines Spielers nach einer Verletzung (gemäss BINA Case Study, CPA-Schritt 4).\n",
                "\n",
                "**Ziel:** Vorhersage von `delta_pct` (Veränderung des Marktwerts in Prozent) basierend auf Alter, Position, Liga, Ausfallzeit und Verletzungshistorie."
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Setup und Bibliotheken laden"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd\n",
                "import numpy as np\n",
                "import matplotlib.pyplot as plt\n",
                "import xgboost as xgb\n",
                "import shap\n",
                "import joblib\n",
                "import os\n",
                "from sklearn.model_selection import train_test_split, cross_validate, KFold\n",
                "from sklearn.linear_model import LinearRegression\n",
                "from sklearn.ensemble import RandomForestRegressor\n",
                "from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score\n",
                "from sklearn.preprocessing import OneHotEncoder\n",
                "from sklearn.compose import ColumnTransformer\n",
                "from sklearn.pipeline import Pipeline\n",
                "import warnings\n",
                "\n",
                "warnings.filterwarnings('ignore')\n",
                "\n",
                "# Random State fixieren für Reproduzierbarkeit (Anforderung)\n",
                "RANDOM_STATE = 42"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Daten laden und aufbereiten\n",
                "Wir laden die Verletzungsdaten und die Marktwert-Historie und führen das Feature-Engineering durch."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Daten laden\n",
                "df_inj = pd.read_csv('Data/cleaned_dataset_final.csv')\n",
                "df_val = pd.read_csv('Data/player_valuations.csv')\n",
                "\n",
                "# Datumsformate anpassen\n",
                "df_inj['injury_from_parsed'] = pd.to_datetime(df_inj['injury_from_parsed'])\n",
                "df_inj['injury_until_parsed'] = pd.to_datetime(df_inj['injury_until_parsed'])\n",
                "df_val['date'] = pd.to_datetime(df_val['date'])\n",
                "\n",
                "print(f\"Verletzungen geladen: {len(df_inj)}\")\n",
                "print(f\"Marktwerte geladen: {len(df_val)}\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Feature Engineering: Verletzungshistorie\n",
                "Wir berechnen die kumulierte Anzahl an früheren Verletzungen und Ausfalltagen pro Spieler."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Zuerst nach Spieler und Datum sortieren\n",
                "df_inj = df_inj.sort_values(['player_id', 'injury_from_parsed'])\n",
                "df_val = df_val.sort_values(['player_id', 'date'])\n",
                "\n",
                "# previous_injuries_count: laufende Nummer der Verletzung (0-basiert)\n",
                "df_inj['previous_injuries_count'] = df_inj.groupby('player_id').cumcount()\n",
                "\n",
                "# total_previous_days_out: Summe der vorherigen Ausfalltage (ohne aktuelle Verletzung)\n",
                "df_inj['Days_clean'] = df_inj['Days'].fillna(0)\n",
                "df_inj['total_previous_days_out'] = df_inj.groupby('player_id')['Days_clean'].apply(lambda x: x.shift().cumsum()).fillna(0)\n",
                "df_inj.drop(columns=['Days_clean'], inplace=True)"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### Target Variable: Marktwertveränderung (delta_pct)\n",
                "Wir ermitteln den Marktwert unmittelbar VOR und NACH der Verletzung, mit einem Mindestabstand von 30 Tagen."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "mv_pre_list = []\n",
                "mv_post_list = []\n",
                "\n",
                "# Iteration über Verletzungen\n",
                "for _, row in df_inj.iterrows():\n",
                "    p_id = row['player_id']\n",
                "    d_from = row['injury_from_parsed']\n",
                "    d_until = row['injury_until_parsed']\n",
                "    \n",
                "    if pd.isna(d_from) or pd.isna(d_until):\n",
                "        mv_pre_list.append(np.nan)\n",
                "        mv_post_list.append(np.nan)\n",
                "        continue\n",
                "        \n",
                "    # Alle Bewertungen des Spielers\n",
                "    p_vals = df_val[df_val['player_id'] == p_id]\n",
                "    \n",
                "    # Marktwert VORHER\n",
                "    pre_vals = p_vals[p_vals['date'] <= d_from]\n",
                "    if pre_vals.empty:\n",
                "        mv_pre_list.append(np.nan)\n",
                "        mv_post_list.append(np.nan)\n",
                "        continue\n",
                "    mv_pre = pre_vals.iloc[-1]['market_value_in_eur']\n",
                "    date_pre = pre_vals.iloc[-1]['date']\n",
                "    \n",
                "    # Marktwert NACHHER (ab Ende der Verletzung, Mindestabstand 30 Tage zu date_pre)\n",
                "    post_vals = p_vals[p_vals['date'] >= d_until]\n",
                "    mv_post = np.nan\n",
                "    for _, post_row in post_vals.iterrows():\n",
                "        if (post_row['date'] - date_pre).days >= 30:\n",
                "            mv_post = post_row['market_value_in_eur']\n",
                "            break\n",
                "            \n",
                "    mv_pre_list.append(mv_pre)\n",
                "    mv_post_list.append(mv_post)\n",
                "\n",
                "df_inj['mv_pre'] = mv_pre_list\n",
                "df_inj['mv_post'] = mv_post_list\n",
                "\n",
                "# Zielvariable berechnen\n",
                "df_inj['delta_pct'] = (df_inj['mv_post'] - df_inj['mv_pre']) / df_inj['mv_pre'] * 100\n",
                "\n",
                "# Filtern fehlender Werte in relevanten Spalten\n",
                "cols_to_check = ['delta_pct', 'mv_pre', 'player_age', 'player_position', 'league', 'injury_category', 'Days', 'Games missed', 'Season']\n",
                "df_ml = df_inj.dropna(subset=cols_to_check).copy()\n",
                "\n",
                "# Ausreisser filtern: delta_pct zwischen -95% und +200%\n",
                "df_ml = df_ml[(df_ml['delta_pct'] >= -95) & (df_ml['delta_pct'] <= 200)]\n",
                "\n",
                "print(f\"Samples nach Bereinigung und Filterung: {len(df_ml)}\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Modellierung (Setup & Training)\n",
                "Wir definieren die Features und trainieren drei Modelle: Lineare Regression (Baseline), Random Forest und XGBoost."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Features definieren\n",
                "numeric_features = ['player_age', 'Days', 'Games missed', 'mv_pre', 'previous_injuries_count', 'total_previous_days_out']\n",
                "categorical_features = ['player_position', 'injury_category', 'league', 'Season']\n",
                "\n",
                "X = df_ml[numeric_features + categorical_features]\n",
                "y = df_ml['delta_pct']\n",
                "\n",
                "# 80/20 Train/Test Split\n",
                "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)\n",
                "\n",
                "# Preprocessing Pipeline\n",
                "preprocessor = ColumnTransformer(\n",
                "    transformers=[\n",
                "        ('num', 'passthrough', numeric_features),\n",
                "        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)\n",
                "    ])\n",
                "\n",
                "# Modelle definieren\n",
                "models = {\n",
                "    'Linear Regression': LinearRegression(),\n",
                "    'Random Forest': RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE),\n",
                "    'XGBoost': xgb.XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=RANDOM_STATE)\n",
                "}\n",
                "\n",
                "# Pipelines\n",
                "pipelines = {}\n",
                "for name, model in models.items():\n",
                "    pipelines[name] = Pipeline([\n",
                "        ('preprocessor', preprocessor),\n",
                "        ('model', model)\n",
                "    ])"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 4. Evaluation\n",
                "Kreuzvalidierung und Auswertung der Metriken auf dem Test-Set.\n",
                "\n",
                "*Hinweis: Erwartete Performance wird nach Training berichtet. Marktwerte hängen von vielen Faktoren ab (Team-Erfolg etc.). Ein R² zwischen 0.25-0.45 ist im Fussball-Kontext realistisch.*"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "results = []\n",
                "kf = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)\n",
                "\n",
                "for name, pipeline in pipelines.items():\n",
                "    # Cross Validation (optional, um Stabilität zu zeigen)\n",
                "    cv_scores = cross_validate(pipeline, X_train, y_train, cv=kf, scoring=('r2', 'neg_mean_absolute_error', 'neg_root_mean_squared_error'))\n",
                "    \n",
                "    # Train & Predict\n",
                "    pipeline.fit(X_train, y_train)\n",
                "    y_pred = pipeline.predict(X_test)\n",
                "    \n",
                "    # Metrics\n",
                "    results.append({\n",
                "        'Model': name,\n",
                "        'CV R² (Mean)': cv_scores['test_r2'].mean(),\n",
                "        'Test R²': r2_score(y_test, y_pred),\n",
                "        'Test MAE': mean_absolute_error(y_test, y_pred),\n",
                "        'Test RMSE': np.sqrt(mean_squared_error(y_test, y_pred))\n",
                "    })\n",
                "\n",
                "df_results = pd.DataFrame(results).round(4)\n",
                "display(df_results)"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 5. Erklärbarkeit mit SHAP\n",
                "SHAP Summary-Plot zur globalen Feature Importance des XGBoost-Modells."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "xgb_pipe = pipelines['XGBoost']\n",
                "X_test_trans = xgb_pipe.named_steps['preprocessor'].transform(X_test)\n",
                "\n",
                "cat_encoder = xgb_pipe.named_steps['preprocessor'].named_transformers_['cat']\n",
                "cat_feature_names = cat_encoder.get_feature_names_out(categorical_features)\n",
                "all_features = numeric_features + list(cat_feature_names)\n",
                "\n",
                "X_test_df = pd.DataFrame(X_test_trans, columns=all_features)\n",
                "\n",
                "explainer = shap.TreeExplainer(xgb_pipe.named_steps['model'])\n",
                "shap_values = explainer(X_test_df)\n",
                "\n",
                "shap.summary_plot(shap_values, X_test_df, plot_type=\"bar\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 6. Modell exportieren\n",
                "Das trainierte Modell wird als `.pkl` Datei gespeichert."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "os.makedirs('models', exist_ok=True)\n",
                "\n",
                "export_data = {\n",
                "    'model_pipeline': pipelines['XGBoost'],\n",
                "    'baseline_pipeline': pipelines['Linear Regression'],\n",
                "    'numeric_features': numeric_features,\n",
                "    'categorical_features': categorical_features\n",
                "}\n",
                "\n",
                "joblib.dump(export_data, 'models/mv_prediction_model.pkl')\n",
                "print(\"Modell-Export nach 'models/mv_prediction_model.pkl' erfolgreich.\")"
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.11.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open("ml_market_value_prediction.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=2, ensure_ascii=False)
