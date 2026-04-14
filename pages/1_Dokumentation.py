import streamlit as st

st.set_page_config(page_title="Dokumentation", page_icon="📖")

st.markdown("# Dokumentation")

st.write("""
Diese Seite dient der Dokumentation der BINA-Fallstudie. Die vier Schritte des CPA Management Accounting Guideline werden hier ausführlich beschrieben.
""")

st.markdown("## 1. Ziele und Informationsbedarf definieren")  # engl. Defning objectives and information needs

st.markdown("## 2. Daten sammeln")  # engl. Collecting data
st.write("""
Um die Verletzungen in den einzelnen europäischen Fussballligen zu analysieren haben wir folgendes öffentlich verfügbares Datenset von Kaggle verwendet:

> Sanan Muzaffarov. (2026). European Football Injuries (2020-2025) [Data set]. Kaggle. https://doi.org/10.34740/KAGGLE/DSV/14465228

### Aufbau
Das Datenset enthält die folgenden Spalten:

| Spaltenbezeichnung    | Spaltenbeschreibung         |
|:--------------------- |:----------------------------|
| Season                | Saison der Liga             |
| Injury                | Art der Verletzung          |
| Days                  | Anzahl der Ausfalltage      |
| Games missed          | verpasste Pflichtspiele     |
| injury_from_parsed    | Startdatum der Verletzung   |
| injury_until_parsed   | Enddatum der Verletzung     |
| player_name           | Name des Spielers           |
| player_age            | Alter des Spielers          |
| player_position       | Position des Spielers       |
| club                  | Verein                      |
| league                | Liga                        |

### Auswahlbegründung
Dieses Datenset wurde ausgewählt, weil es:
* öffentlich zugänglich ist,
* umfangreiche und strukturierte Daten liefert,
* die für unsere Analyse relevanten Informationen enthält (z. B. Spieler, Verletzungen, Ausfallzeiten, Liga, Position),
* und dadurch die Untersuchung verschiedener Fragestellungen im Zusammenhang mit Verletzungen im Profisport ermöglicht.

Beispielsweise lassen sich mit dem Datenset unter anderem folgende Fragen untersuchen:
* Welche Spieler sind besonders verletzungsanfällig («Pechvögel»)?
* Welche Verletzungsarten führen zu wie vielen Ausfalltagen?
* Welche Spielerpositionen sind am stärksten von Verletzungen betroffen?
* Gibt es Unterschiede zwischen Ligen, Vereinen oder Altersgruppen?
* Treten bestimmte Verletzungen bei gewissen Positionen häufiger auf?
* Wie haben sich die Verletzungsmuster über die Saisons hinweg verändert?
* Welche Spieler haben die meisten Spiele aufgrund von Verletzungen verpasst?
* Gibt es Spieler, die trotz Verletzungen eine hohe Anzahl an Spielen absolviert haben?
* Welche Vereine haben die meisten verletzungsbedingten Ausfälle zu verzeichnen?     

### Datenbeschaffung und -überprüfung
Bevor das Datenset für die Analyse verwendet wurde, haben wir geprüft:
* Ob das Datenset alle identifizierten Informationsbedarfe aus Schritt 1 abdeckt
* Ob das Datenset zuverlässig und konsistent strukturiert ist

### Bereinigung und Standardisierung
Vor der Analyse wurden die Daten bereinigt und standardisiert:
* Alphanumerische Werte in Spalten bereinigen (z. B. «10 days» zu «10»)
* Datenformat anpassen und nachkommende Leerzeichen entfernen
* Kodierungsfehler bei Umlauten (z. B. «Ã©»)
* Unterschiedliche Schreibweisen der Ligen (z. B. «Tottenham» vs. «Tottenham Hotspur» oder «Bochum» vs. «Vfl Bochum»)
* Verletzungen vereinheitlichen durch Kleinschreibung
""")

st.markdown("## 3. Daten analysieren")  # engl. Analyzing data

st.markdown("## 4. Informationen präsentieren")  # engl. Presenting information