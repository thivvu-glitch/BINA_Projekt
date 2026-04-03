# Verletzunganalyse App

Dieses Projekt analysiert europäische Fussball-Verletzungen von 2020 bis 2025.

## Voraussetzungen

- uv installiert: https://docs.astral.sh/uv/getting-started/installation/
- Python 3.11 (wird automatisch durch uv bereitgestellt)

## Setup mit uv

Es gibt zwei mögliche Wege für die Installation:

1. Direkter uv-Workflow (empfohlen):

```bash
uv sync
```

Bei OneDrive-Pfaden kann `uv sync` mit Hardlink-Fehlern scheitern. Dann stattdessen:

```bash
uv sync --link-mode=copy
```

2. Setup-Skript:

```bash
uv run install.py
```

Beide Varianten erstellen/verwenden `.venv` und installieren alle benötigten Pakete.

Abhängigkeiten werden ausschliesslich aus `pyproject.toml` gelesen.

## Virtuelle Umgebung aktivieren

PowerShell (Windows):

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

## Applikation starten

Datensatz zuerst bereinigen:

```bash
uv run python data_clean.py
```

Dieser Schritt erstellt/aktualisiert `cleaned_dataset_final.csv`, das vom Dashboard geladen wird.

Streamlit Seite:

```bash
uv run streamlit run Home.py
```

Analyse-Skript (optional):

```bash
uv run python analyze_injuries.py
```

## Projektstruktur

- `dashboard.py`: Interaktives Streamlit-Dashboard für Visualisierungen.
- `analyze_injuries.py`: Statistische Analyse und Erstellung von Grafiken.
- `install.py`: Setup-Skript für uv + Python 3.11 + Installation.
- `pyproject.toml`: uv-Projektkonfiguration und Python-Version.
- `output/`: Ausgabeordner für generierte Grafiken.
- `Data/`: Input-Daten als csv.
