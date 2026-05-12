# Machine Learning: Marktwert-Impact-Vorhersage

Diese Erweiterung des BINA-Dashboards beinhaltet ein XGBoost-Modell zur Vorhersage des prozentualen Marktwertverlusts eines Spielers nach einer Verletzung.

## Architektur & Dateien
1. `ml_market_value_prediction.ipynb`: Detailliertes Jupyter Notebook für Exploration, Feature-Engineering und Visualisierung.
2. `scripts/train_model.py`: Automatisierbares Python-Skript für das regelmässige Training des Modells. Speichert das fertig trainierte Modell in `models/mv_prediction_model.pkl`.
3. `scripts/ml_predict.py`: Hilfsmodul für das Dashboard zur Generierung der Echtzeit-Vorhersagen und SHAP-Werte.
4. `pages/2_Dashboard.py`: Enthält den neuen interaktiven Tab "Verletzungs-Simulator" inklusive KPI-Karten, Handlungsempfehlungen und SHAP-Wasserfall-Diagramm.
5. `pyproject.toml`: Wurde um die erforderlichen Abhängigkeiten (`scikit-learn`, `xgboost`, `shap`, `joblib`) erweitert.

## Ausführungs-Anleitung (Schritt-für-Schritt)

### 1. Abhängigkeiten installieren
Stelle sicher, dass alle neuen Pakete im Projekt installiert sind. Falls du `uv` nutzt, führe folgenden Befehl im Terminal aus:
```bash
uv sync
```
*(Alternativ über Pip: `pip install scikit-learn xgboost shap joblib`)*

### 2. Modell trainieren
Bevor der Simulator im Dashboard genutzt werden kann, muss das ML-Modell einmalig trainiert und als `.pkl`-Datei generiert werden. Führe dazu dieses Kommando aus:
```bash
python scripts/train_model.py
```
*(Hinweis: Dieser Schritt wurde durch deinen virtuellen KI-Assistenten bereits automatisch durchgeführt. Die Datei `models/mv_prediction_model.pkl` existiert bereits!)*

### 3. Dashboard starten
Starte (oder aktualisiere) das Streamlit-Dashboard wie gewohnt:
```bash
streamlit run Home.py
```
Navigiere dann oben in der Tab-Leiste zu **"Verletzungs-Simulator"**. 

### 4. Interpretation (SHAP)
Der Simulator gibt nicht nur einen Prozentwert aus, sondern auch einen **SHAP-Wasserfall-Plot**. Dieser zeigt an, wie stark welches Merkmal die finale Prognose beeinflusst hat. 
- Rote Balken = Wertmindernd (stärkerer Drop)
- Blaue Balken = Wertsteigernd bzw. abfedernd (geringerer Drop)
