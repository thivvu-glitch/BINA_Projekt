# Verletzunganalyse App

Dieses Projekt analysiert europäische Fußball-Verletzungen von 2020 bis 2025.

## Voraussetzungen

Stellen Sie sicher, dass Python installiert ist. Es wird empfohlen, die virtuelle Umgebung zu verwenden.

## Starten der Applikation

Folgen Sie diesen Schritten, um die Applikation zu starten:

1. **Virtuelle Umgebung aktivieren:**
   ```bash
   source venv/bin/activate
   ```

2. **Interaktives Dashboard starten:**
   ```bash
   streamlit run dashboard.py
   ```

3. **Analyse-Skript ausführen (optional):**
   ```bash
   python analyze_injuries.py
   ```

## Projektstruktur

- `dashboard.py`: Das interaktive Streamlit-Dashboard für Visualisierungen.
- `analyze_injuries.py`: Ein Python-Skript für die statistische Analyse und Erstellung von Grafiken.
- `venv/`: Die virtuelle Umgebung mit allen benötigten Bibliotheken (pandas, streamlit, plotly, etc.).
