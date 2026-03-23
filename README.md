# Verletzunganalyse App

Dieses Projekt analysiert europaeische Fussball-Verletzungen von 2020 bis 2025.

## Voraussetzungen

- uv installiert: https://docs.astral.sh/uv/getting-started/installation/
- Python 3.11 (wird automatisch durch uv bereitgestellt)

## Setup mit uv

Es gibt zwei moegliche Wege fuer die Installation:

1. Direkter uv-Workflow (empfohlen):

```bash
uv sync
```

2. Setup-Skript:

```bash
uv run install.py
```

Beide Varianten erstellen/verwenden `.venv` und installieren alle benoetigten Pakete.

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

Interaktives Dashboard:

```bash
uv run streamlit run dashboard.py
```

Analyse-Skript (optional):

```bash
uv run python analyze_injuries.py
```

## Projektstruktur

- `dashboard.py`: Interaktives Streamlit-Dashboard fuer Visualisierungen.
- `analyze_injuries.py`: Statistische Analyse und Erstellung von Grafiken.
- `requirements.txt`: Abhaengigkeiten fuer pip/uv pip.
- `install.py`: Setup-Skript fuer uv + Python 3.11 + Installation.
- `pyproject.toml`: uv-Projektkonfiguration und Python-Version.
- `output/`: Ausgabeordner fuer generierte Grafiken.
