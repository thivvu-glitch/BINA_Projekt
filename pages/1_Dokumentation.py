import streamlit as st

st.set_page_config(page_title="Dokumentation", page_icon="📖")

st.markdown("# Dokumentation")

st.write("""
Diese Seite dient der Dokumentation der BINA-Fallstudie. Die vier Schritte des CPA Management Accounting Guideline werden hier ausführlich beschrieben.
""")

st.markdown("## 1. Ziele und Informationsbedarf definieren")  # engl. Defning objectives and information needs

st.write("""
Verletzungen im Fussball haben einen wesentlichen Einfluss auf die sportliche Leistungsfähigkeit, die Zusammenstellung von Teams sowie auf medizinische und organisatorische Ressourcen. Unser Dashboard sollen Informationen zu folgenden fünf **Hauptfragen** liefern:
- Wie entwickeln sich Verletzungen im Profifussball über Zeit und Wettbewerbe hinweg?
- Welche Muster zeigen sich bei Verletzungen nach Position, Körperregion und Liga?
- Welche Verletzungsarten sind sportlich und wirtschaftlich am kritischsten?
- Wie beeinflussen Verletzungen den Marktwert von Spielern?
- Welche Massnahmen liefern den grössten Return im Umgang mit Verletzungen?
         
Daraus lässt sich das **strategische Ziel** der Arbeit ableiten: Auf Basis der Daten sollen fundierte Erkenntnisse für datenbasierte Entscheidungen im Profifussball gewonnen werden, um Verletzungsrisiken gezielt zu reduzieren, wirtschaftliche Auswirkungen zu minimieren und Investitionen in Prävention, Rehabilitation sowie Spielertransfers strategisch zu optimieren.

Die detaillierten Fragestellungen sind in den dazugehörigen Dashboards erwähnt:
         """)
st.page_link("pages/2_Dashboard.py", label="Zu den Dashboards", query_params={"tab": "Zeitvergleich & Trends"}, icon="📈")

st.markdown("## 2. Daten sammeln")  # engl. Collecting data
st.write("""
#### Datenbasis und Datenquellen
Die vorliegende Analyse basiert auf mehreren öffentlich zugänglichen Datensätzen, welche über die Plattform Kaggle bereitgestellt werden. Ziel der Analyse ist es, Verletzungsereignisse im Profifussball umfassend zu untersuchen. Dabei stehen sowohl die Analyse von Verletzungsmustern (z. B. betroffene Körperteile, Ausfallzeiten und positionsspezifische Unterschiede) als auch der Einfluss von Verletzungen auf die Entwicklung des Marktwerts von Spielern im Fokus.

Für die Analyse wurden folgende externe, sekundäre Datenquellen verwendet:

> Sanan Muzaffarov. (2026). European Football Injuries (2020-2025) [Data set]. Kaggle. https://doi.org/10.34740/KAGGLE/DSV/14465228

> David Cariboo. (2026). Football Data from Transfermarkt [Data set]. Kaggle. https://www.kaggle.com/datasets/davidcariboo/player-scores/data

Diese Datensätze wurden miteinander kombiniert, um eine integrierte Analyse von sportlichen Ereignissen (Verletzungen) und ökonomischen Kennzahlen (Marktwertentwicklung) zu ermöglichen.


#### Struktur und Klassifikation der Daten
Die hier verwendeten Daten liegen in strukturierter Form (CSV-Format) vor. Sie sind tabellarisch angeordnet und somit für Analysezwecke gut geeignet. Teilweise wurden einzelne Datenbereinigungen vorgenommen, sodass die Werte atomar vorliegen (z. B. «10 days» → «10») oder unterschiedliche Schreibweisen vereinheitlicht (z. B. «Tottenham» vs. «Tottenham Hotspur»).

Inhaltlich lassen sich die Daten in drei zentrale Kategorien einteilen:

* **Ereignisdaten**: Verletzungen, Ausfallzeiten und verpasste Spiele
* **Stammdaten**: Informationen zu Spielern und Vereinen (z. B. Alter, Position, Vereinszugehörigkeit)
* **Zeitreihendaten**: Entwicklung des Marktwerts über verschiedene Zeitpunkte hinweg

Mehrheitlich handelt es sich hier um quantitative Daten, ergänzt durch kategoriale Variablen (z. B. Liga, Position oder Verein). Dadurch sind sowohl deskriptive als auch erklärende Analysen möglich.


#### Beschreibung der Datensätze
Im Folgenden werden die verwendeten Datensätze sowie deren Spalten beschrieben:

**Datenset «full_dataset_thesis - 1.csv»**, Quelle: European Football Injuries (2020-2025)

| Variable              | Beschreibung                                      |
|:--------------------- |:--------------------------------------------------|
| Season                | Saison der Liga                                   |
| Injury                | Art der Verletzung                                |
| Days                  | Anzahl der Ausfalltage                            |
| Games missed          | Anzahl verpasster Pflichtspiele                   |
| injury_from_parsed    | Startdatum der Verletzung                         |
| injury_until_parsed   | Enddatum der Verletzung                           |
| player_name           | Name des Spielers                                 |
| player_age            | Alter des Spielers zum Zeitpunkt der Verletzung   |
| player_position       | Position des Spielers                             |
| club                  | Verein                                            |
| league                | Liga                                              |


**Datenset «players.csv»**, Quelle: Football Data from Transfermarkt

| Variable                               | Beschreibung                            |
|:-------------------------------------- |:----------------------------------------|
| player_id                              | Eindeutige Spieler-ID                   |
| first_name                             | Vorname                                 |
| last_name                              | Nachname                                |
| name                                   | Vollständiger Name                      |
| last_season                            | Letzte erfasste Saison                  |
| current_club_id                        | ID des aktuellen Vereins                |
| player_code                            | Eindeutiger Spieler-Code                |
| country_of_birth                       | Geburtsland                             |
| city_of_birth                          | Geburtsstadt                            |
| country_of_citizenship                 | Staatsbürgerschaft                      |
| date_of_birth                          | Geburtsdatum                            |
| sub_position                           | Detaillierte Positionsangabe            |
| position                               | Hauptposition                           |
| foot                                   | Bevorzugter Fuss                        |
| height_in_cm                           | Körpergrösse in cm                      |
| contract_expiration_date               | Vertragsenddatum                        |
| agent_name                             | Name des Spielerberaters                |
| image_url                              | URL zum Spielerbild                     |
| international_caps                     | Anzahl Länderspiele                     |
| international_goals                    | Anzahl Tore im Nationalteam             |
| current_national_team_id               | ID des aktuellen Nationalteam           |
| url                                    | Link zum Spielerprofil                  |
| current_club_domestic_competition_id   | ID des nationalen Wettbewerbs           |
| current_club_name                      | Name des aktuellen Vereins              |
| market_value_in_eur                    | Aktueller Marktwert in Euro             |
| highest_market_value_in_eur            | Höchster erreichter Marktwert in Euro   |


**Datenset «player_valuations.csv»**, Quelle: Football Data from Transfermarkt

| Variable                              | Beschreibung                                 |
|:------------------------------------- |:---------------------------------------------|
| player_id                             | Eindeutige Spieler-ID                        |
| date                                  | Datum der Marktwertbewertung                 |
| market_value_in_eur                   | Marktwert in Euro zum jeweiligen Zeitpunkt   |
| current_club_name                     | Vereinsname zum Bewertungszeitpunkt          |
| current_club_id                       | Vereins-ID zum Bewertungszeitpunkt           |
| player_club_domestic_competition_id   | ID des nationalen Wettbewerbs                |


**Datenset «clubs.csv»**, Quelle: Football Data from Transfermarkt

| Variable                  | Beschreibung                                |
|:------------------------- |:--------------------------------------------|
| club_id                   | Eindeutige Vereins-ID                       |
| club_code                 | Vereinscode                                 |
| name                      | Vereinsname                                 |
| domestic_competition_id   | ID des nationalen Wettbewerbs               |
| total_market_value        | Gesamtmarktwert                             |
| squad_size                | Kadergrösse                                 |
| average_age               | Durchschnittsalter                          |
| foreigners_number         | Anzahl ausländischer Spieler                |
| foreigners_percentage     | Anteil ausländischer Spieler (%)            |
| national_team_players     | Anzahl Nationalspieler                      |
| stadium_name              | Stadionname                                 |
| stadium_seats             | Anzahl Sitzplätze im Stadion                |
| net_transfer_record       | Transferbilanz (Einnahmen minus Ausgaben)   |
| coach_name                | Name des Trainers                           |
| last_season               | Letzte erfasste Saison                      |
| filename                  | Dateiname                                   |
| url                       | Link zur Vereinsseite                       |


**Datenset «game_events.csv»**, Quelle: Football Data from Transfermarkt

| Variable                  | Beschreibung                                           |
|:------------------------- |:-------------------------------------------------------|
| game_event_id             | Eindeutige Spielereignis-ID                            |
| date                      | Datum des Spiels                                       |
| game_id                   | Eindeutige Spiel-ID                                    |
| minute                    | Spielminute, in der das Ereignis stattgefunden hat     |
| type                      | Art des Ereignisses (z. B. Goals, Karten)              |
| club_id                   | Eindeutige Vereins-ID                                  |
| club_name                 | Name des Vereins                                       |
| player_id                 | Eindeutige Spieler-ID                                  |
| description               | Beschreibung des Ereignisses (z. B. gelbe Karte, Foul) |
| player_in_id              | ID des eingewechselten Spielers                        |
| player_assist_id          | ID des Spielers, der die Vorlage gegeben hat           |


**Datenset «game_lineups.csv»**, Quelle: Football Data from Transfermarkt

| Variable                  | Beschreibungs                                                 |
|:------------------------- |:--------------------------------------------------------------|
| game_lineups              | Eindeutige Lineup-ID                                          |
| date                      | Datum des Spiels                                              |
| game_id                   | Eindeutige Spiel-ID                                           |
| player_id                 | Eindeutige Spieler-ID                                         |
| club_id                   | Eindeutige Vereins-ID                                         |
| player_name               | Name des Spielers                                             |
| type                      | Art des Einsatzes                                             |
| position                  | Spielposition des Spielers                                    |
| number                    | Nummer des Spielers                                           |
| team_captain              | Kennzeichnung, ob Spieler Captain (1) oder Mannschaft (0) war |


**Datenset «games.csv»**, Quelle: Football Data from Transfermarkt

| Variable                  | Beschreibung                                                  |
|:------------------------- |:--------------------------------------------------------------|
| game_id                   | Eindeutige Spiel-ID                                           |
| competition               | Name des Wettbewerbs                                          |
| season                    | Saison, in der das Spiel stattgefunden hat                    |
| round                     | Spieltag bzw. Runde innerhalb der Saison                      |
| date                      | Datum des Spiels                                              |
| home_club_id              | Eindeutige Heimmannschaft-ID                                  |
| away_club_id              | Eindeutige Auswärtsmannschaft-ID                              |
| home_club_goals           | Anzahl erzielter Tore der Heimmannschaft                      |
| away_club_goals           | Anzahl erzielter Tore der Auswärtsmannschaft                  |
| home_club_position        | Tabellenplatz der Heimmannschaft zum Zeitpunkt des Spiels     |
| away_club_position        | Tabellenplatz der Auswärtsmannschaft zum Zeitpunkt des Spiels |
| home_club_manager_name    | Name des Trainers der Heimmannschaft                          |
| away_club_manager_name    | Name des Trainers der Auswärtsmannschaft                      |
| stadium                   | Name des Stadions                                             |
| attendance                | Zuschauerzahl beim Spiel                                      |
| referee                   | Name des Schiedsrichters                                      |
| url                       | Link zum Spiel                                                |
| home_club_formation       | Startformation der Heimmannschaft                             |
| away_club_formation       | Startformat der Auswärtsmannschaft                            |
| home_club_name            | Name der Heimmannschaft                                       |
| away_club_name            | Name der Auswärtsmannschaft                                   |
| aggregate                 | Gesamtergebnis über mehrere Spiele                            |
| competition_type          | Art des Wettbewerbs                                           |


#### Relevanz der Datensätze
Die ausgewählten Datensätze ermöglichen eine mehrdimensionale Analyse von Verletzungen im Profifussball. Dabei können insbesondere folgende Aspekte untersucht werden:

* Verteilung und Verletzungen nach **Körperregionen**
* Zusammenhang zwischen **Spielerposition und Verletzungsanfälligkeit**
* Analyse von **Ausfallzeiten und deren Ursachen**
* Unterschiede zwischen **Ligen, Vereinen und Altersgruppen**
* Einfluss von Verletzungen auf die **Marktwertentwicklung**

Durch die Verknüpfung der Datensätze können sowohl sportliche als auch ökonomische Einflussfaktoren berücksichtigt werden.


#### Datenbeschaffung und Datenzugang
Die Datensätze wurden über die Plattform Kaggle bezogen und als CSV-Dateien heruntergeladen. Es handelt sich dabei um statische Daten, die nicht in Echtzeit aktualisiert werden und keine API-basierte Anbindung erfordern. Lediglich für die Anzeige von Spielerbildern ist eine Internetverbindung notwendig.

#### Zeitliche Struktur der Daten
Die verwendeteten Datensätze weisen unterschiedliche zeitliche Dimensionen auf:

* **Verletzungsdaten**: Zeitraum von 2020 bis 2025
* **Marktwertdaten**: wiederholte Beobachtungen über mehrere Zeitpunkte hinweg
* **Stammdaten**: punktuelle Informationen zu Spielern und Vereinen


#### Datenaufbereitung und Datenstandardisierung
Im Rahmen der Datenaufbereitung wurden die Datensätze bereinigt und standardisiert, um eine konsistente und analysierbare Datenbasis zu gewährleisten.

Am Beispiel des Datensatzes «full_dataset_thesis - 1.csv» wurden folgende Schritte durchgeführt:
* Bereinigung alphanumerische Werte (z. B. «10 days» → «10»)
* Anpassung von Datenformaten und Entfernen von Leerzeichen (nach dem Text)
* Korrektur von Kodierungsfehlern bei Umlauten (z. B. «Ã©»)
* Vereinheitlichung von Schreibweisen (z. B. «Tottenham» vs. «Tottenham Hotspur» oder «Bochum» vs. «Vfl Bochum»)
* Standardisierung der Verletzungsbezeichnungen durch Kleinschreibung

Diese Schritte stellen sicher, dass die Daten in einer einheitlichen Struktur vorliegen und für die anschliessende Analyse zuverlässig verwendet werden können.
""")

st.markdown("## 3. Daten analysieren")  # engl. Analyzing data

st.write('''
Mithilfe der Dahsboards können verschiedene Analysen durchgeführt werden, um z. B. Verletzungsereignisse im Profifussball zu untersuchen
und deren Einfluss auf den Marktwert der Spieler zu analysieren.

Beschreibung einzelner Laschen des Dashboards:

#### Zeitvergleich und Trends:
* **Zielgruppe:**  Sportdirektoren, Trainern und medizinische Abteilungen. 
* **Nutzen:** Mit diesem Tool können die Anspruchsgruppen die Verlertzungswahrscheinlichkeit bei Grossturnieren  und Ausfallzeiten über Saisons zwecks Ressourcenplanung analysieren.
* **Besonderheit:** Stratified Matching: Vergleich von gleichwertigen Spielern für die Analyse von Verletzungsmustern.
* **Wichtig für Kohortenvergleich:** Bei den Filtern müssen unterschiedliche Saisons ausgewählt werden, um sinnvolle Ergebnisse zu erhalten und Vergleiche durchführen zu können.

#### Interaktives Spielfeld:
* **Zielgruppe:** Trainer, Athletik-Trainer, Postionscoaches und Scouts.
* **Nutzen:** Virtuelles Fussballspielfeld mit Spielerpositionen und Verletzungsereignissen. Leistet Hilfestellung für Aufstellung und Spielerroation.
* **Besonderheit:** Verknüpfung mit Körperregionen, wenn auf eine Spielerposition geklickt wird.

#### Interaktive Körperregionen:
* **Zielgruppe:** Medizinisches Personal, Physiotherapeuten, Sportmediziner und Forscher.
* **Nutzen:** Mapping von Verletzungen auf Körperregionen, Visualisierung von anatomischen Schwachpunkten bzw. hochbeanspruchten Körperregionen.
* **Verlinkung:** mit Karten inklusiver Rangliste von Ausfalltagen für eine bestimmte Verletzungregion, aufgeschlüsselt nach Spieler, Position innerhalb der Liga

#### Clubanalyse:
* **Zielgruppe:** Führungsetage und medizinisches Personal.
* **Nutzen:** Kader-Risikoexposition, Unterstützung von Vertrags- und Investitionsentscheidungen, mögliche ROI von medizinischen investitionen und Spielertransfers

#### Marktwert- und Risikoanalyse:
* **Zielgruppe:** Führungsetage, Contract-Manager, Sportdirektoren und Scouts.
* **Nutzen:** Analyse des wirtschaftlichen Risikos von Verletzungen, Zusammenhang zwischen Verletzungen und Marktwert, Identifikation von Spielern mit hohem Verletzungsrisiko und wirtschaftlichem Potenzial.
* **Besonderheit:** Verknüpfung von Verletzungsdaten mit Marktwertdaten, um die wirtschaftlichen Auswirkungen von Verletzungen zu analysieren.

#### Verletzungssimulator:
* **Zielgruppe:** Führungsetage, Contract-Manager, Sportdirektoren und Scouts.
* **Nutzen:** Simuliert verschiedene Verletzungsszenarien und analysiert deren wirtschaftliche Auswirkungen, unterstützt bei der Entscheidungsfindung im Umgang mit Verletzungen.
* **Besonderheit:** Interaktive Simulation basierend auf einer Machine-Learning-Prognose von Verletzungsszenarien, Analyse der wirtschaftlichen Auswirkungen auf Spieler und Vereine.        
''')

st.markdown("## 4. Informationen präsentieren")  # engl. Presenting information

st.write('''
Die Informationen werden im Dashboard präsentiert.
''')
st.page_link("pages/2_Dashboard.py", label="Zu den Dashboards", query_params={"tab": "Zeitvergleich & Trends"}, icon="📈")

st.markdown("## 5. Datengetriebene Entscheidungen treffen") 

st.write('''
Mittels Machine-Learing-Modellen sollen Vorhersagen zur Entwicklung des Marktwerts nach Verletzungen möglich werden. Dafür wurde ein ML-Modell mit den vorhandenen Daten trainiert und das entsprechende Dashboard «Verletzungssimulator» erstellt:
         ''')
st.page_link("pages/2_Dashboard.py", label="Zum Verletzungssimulator", query_params={"tab": "Verletzungssimulator"}, icon="🔮")