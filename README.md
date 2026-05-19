# Europäische Fussballverletzungen (2020-2025)

Dieses Business Intelligence Dashboard ermöglicht die Analyse von Verletzungsmustern im europäischen Profifussball. Das Projekt basiert auf der **CPA Management Accounting Guideline** für datengesteuerte Entscheidungen.

Diese Fallstudie wurde im Rahmen des Moduls BINA im FS2026 des Masterstudiengangs Wirtschaftsinformatik realisiert.

## Features

- 📊 **Interaktives Dashboard** mit mehreren Analyse-Perspektiven
- 🏥 **Verletzungsanalyse** nach Körperregion, Position und Saison
- 📈 **Trend- und Zeitvergleich** (z. B. Impact von WM/EM)
- 🔮 **Machine Learning Simulator** zur Vorhersage von Marktwertverlusten nach Verletzungen
- 🧠 **SHAP-Erklärbarkeit** für transparente ML-Vorhersagen
- 📚 **Umfassende Dokumentation** der BINA-Methodik

## Voraussetzungen

- uv installiert: https://docs.astral.sh/uv/getting-started/installation/
- Python 3.11 (wird automatisch durch uv bereitgestellt)
- git lfs: https://git-lfs.com/
- (Nur MacOS) libomp: brew install libomp

## Installation

### 1. Daten über git lfs herunterladen

```bash
git lfs install
git lfs pull
git lfs checkout
```

### 2. Abhängigkeiten installieren

```bash
uv sync
```

Falls `uv sync` mit Hardlink-Fehlern bei OneDrive-Pfaden scheitert:

```bash
uv sync --link-mode=copy
```

## Verwendung

### Datensatz vorbereiten (einmalig)

```bash
uv run python data_clean.py
```

Dieser Schritt bereinigt die Rohdaten und erstellt `Data/cleaned_dataset_final.csv`.

### Machine Learning Modell trainieren (optional, da trainiertes Modell schon dabei ist)

```bash
uv run python machine_learning/train_model.py
```

Trainiert das XGBoost-Modell für Marktwert-Vorhersagen und speichert es in `machine_learning/models/`.

### Dashboard starten

```bash
uv run streamlit run Home.py
```

Das Dashboard öffnet sich im Browser und bietet folgende Seiten:

- **Home**: Übersicht und Navigation
- **Dokumentation**: Detaillierte Beschreibung der Methodik
- **Dashboard**: Interaktive Analysen
  - Zeitvergleich & Trends
  - Spielfeldanalyse
  - Körperregionanalyse
  - Verletzungs-Simulator (ML)

## Projektstruktur

```
├── Home.py                          # Streamlit Einstiegspunkt
├── data_clean.py                    # Datenbereinigungs-Pipeline
├── pages/
│   ├── 1_Dokumentation.py           # BINA-Fallstudie Dokumentation
│   └── 2_Dashboard.py               # Hauptanalyse-Dashboard
├── machine_learning/
│   ├── train_model.py               # ML-Modell Training
│   ├── ml_predict.py                # Vorhersage-Modul
│   ├── README_ML.md                 # ML-Dokumentation
│   └── models/                      # Trainierte Modelle (pkl-Dateien)
├── scripts/
│   ├── analyze_injuries.py          # Detaillierte Analyse-Skripte
│   └── ...                          # Weitere Utility-Skripte
├── Data/
│   ├── cleaned_dataset_final.csv    # Prozessierter Datensatz
│   └── ...                          # Rohdaten (CSV)
├── assets/                          # Statische Medien-Ressourcen (Bodymap & Bilder)
├── reports/                         # Generierte Reports und Duplikat-Analysen
├── output/                          # Generierte Grafiken und Outputs
├── tests/                           # Unit-Tests
├── Archiv/                          # Archivierte, ungenutzte Datensätze und Altlasten
├── pyproject.toml                   # Projekt-Dependencies und uv-Konfiguration
└── README.md                        # Diese Datei
```

## Technologie-Stack

- **Streamlit**: Web-Framework für interaktive Dashboards
- **Pandas**: Datenmanipulation und -analyse
- **XGBoost**: Machine Learning für Vorhersagen
- **SHAP**: Explainable AI für Modell-Interpretierbarkeit
- **Plotly**: Interaktive Datenvisualisierung
- **Scikit-learn**: ML-Utilities und Preprocessing

## Datensätze

Das Projekt nutzt folgende externe Quellen:

> Sanan Muzaffarov. (2026). European Football Injuries (2020-2025) [Data set]. Kaggle. https://doi.org/10.34740/KAGGLE/DSV/14465228

> David Cariboo. (2026). Football Data from Transfermarkt [Data set]. Kaggle. https://www.kaggle.com/datasets/davidcariboo/player-scores/data

Weitere Informationen zur Datenstruktur und Klassifikation befinden sich in der **Dokumentation** im Dashboard.
