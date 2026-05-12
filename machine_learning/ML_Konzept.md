# Machine-Learning-Konzept: Marktwert-Impact-Vorhersage bei Verletzungen

## 1. Ausgangslage und Zielsetzung

Im Rahmen der BINA-Fallstudie wird ein Machine-Learning-Modell konzipiert, das den finanziellen Einfluss einer Verletzung auf den Marktwert eines Profifussballers vorhersagt. Die zentrale Fragestellung lautet:

> *Wenn ein Spieler mit den Eigenschaften X (Alter, Position, Liga, Vorgeschichte) sich die Verletzung Y zuzieht, wie stark wird sein Marktwert voraussichtlich sinken?*

Diese Vorhersage erweitert das bestehende Streamlit-Dashboard um eine prädiktive Komponente und übersetzt damit das in der Auswertung verwendete deskriptive Delta-Verfahren in ein verallgemeinerbares Vorhersagemodell.

## 2. Einordnung des ML-Problems

Es handelt sich um ein **überwachtes Machine-Learning-Problem (Supervised Learning)** vom Typ **Regression**, da eine kontinuierliche Zielvariable (prozentualer Marktwertverlust in Prozent) vorhergesagt werden soll. Die Trainingsdaten enthalten sowohl die Eingangsmerkmale (Features) als auch das beobachtete Ergebnis (Marktwert-Delta), wodurch ein gelabeltes Lernverfahren möglich wird.

## 3. Auswahl des Algorithmus

Für die Modellierung wurden mehrere Algorithmen in Betracht gezogen und gegeneinander abgewogen:

### 3.1 Empfohlener Hauptalgorithmus: Gradient Boosting (XGBoost)

**XGBoost (Extreme Gradient Boosting)** ist die methodisch passendste Wahl für die vorliegenden Daten. Begründung:

- **Tabellarische Daten:** Die Datensätze liegen in strukturierter Form mit gemischten numerischen und kategorialen Merkmalen vor. Baumbasierte Ensemble-Verfahren erzielen bei dieser Datenstruktur empirisch die besten Resultate (vgl. Grinsztajn et al., 2022, NeurIPS).
- **Robustheit:** Das Verfahren ist tolerant gegenüber Ausreissern, fehlenden Werten und unterschiedlichen Wertebereichen.
- **Industriestandard:** XGBoost wird in der Finanz-, Versicherungs- und Sportanalytikbranche produktiv eingesetzt und gewinnt regelmässig Kaggle-Wettbewerbe.
- **Erklärbarkeit:** In Kombination mit SHAP-Werten (Shapley Additive exPlanations) lässt sich jede einzelne Vorhersage transparent aufschlüsseln.

### 3.2 Baseline-Modell: Lineare Regression

Als methodischer Vergleichsmassstab wird eine **multivariate lineare Regression** trainiert. Sie dient nicht als finales Modell, sondern als Plausibilitäts-Check: Erst wenn XGBoost die einfache Baseline messbar übertrifft, ist der Mehraufwand des komplexeren Modells gerechtfertigt.

### 3.3 Verworfene Alternativen

| Alternative | Grund für Verwerfung |
|---|---|
| Deep Learning (Neuronale Netze) | Bei tabellarischen Daten dieser Grössenordnung empirisch unterlegen, hoher Rechenaufwand, schwer interpretierbar |
| Klassifikation (z. B. «Hoher / niedriger Verlust») | Verliert quantitative Information, die für Vertragsverhandlungen entscheidend ist |
| Klassische Zeitreihenmodelle (ARIMA) | Setzt regelmässige Zeitabstände voraus, die in Verletzungsdaten nicht gegeben sind |

## 4. Datengrundlage und Feature-Engineering

Die Trainingsdaten werden aus den bereits aufbereiteten Quellen (`cleaned_dataset_final.csv` und `player_valuations.csv`) abgeleitet. Pro historischer Verletzung entsteht ein Trainings-Sample mit folgenden Merkmalen:

### 4.1 Eingangsmerkmale (Features)

| Feature | Datentyp | Quelle | Beschreibung |
|---|---|---|---|
| `player_age` | numerisch | Verletzungs-Datensatz | Alter zum Zeitpunkt der Verletzung |
| `player_position` | kategorisch | Verletzungs-Datensatz | Spielposition (z. B. Centre-Back) |
| `injury_category` | kategorisch | Verletzungs-Datensatz | Verletzungskategorie (z. B. Knee, Muscle) |
| `injury_type` | kategorisch | Verletzungs-Datensatz | Spezifische Verletzung (z. B. cruciate ligament rupture) |
| `days_out` | numerisch | Verletzungs-Datensatz | Anzahl Ausfalltage |
| `league` | kategorisch | Verletzungs-Datensatz | Liga (z. B. Premier League) |
| `market_value_pre` | numerisch | Marktwert-Datensatz | Marktwert unmittelbar vor der Verletzung |
| `previous_injuries_count` | numerisch (berechnet) | Verletzungs-Historie | Anzahl vorheriger Verletzungen des Spielers |
| `total_previous_days_out` | numerisch (berechnet) | Verletzungs-Historie | Kumulierte Ausfalltage vor dieser Verletzung |
| `season` | kategorisch | Verletzungs-Datensatz | Saison der Verletzung |

### 4.2 Zielvariable (Target)

| Zielgrösse | Definition |
|---|---|
| `delta_pct` | `(Marktwert_nach − Marktwert_vor) / Marktwert_vor × 100` |

Optional kann zusätzlich die absolute Marktwertveränderung in Euro (`delta_eur`) als zweite Zielvariable trainiert werden, um sowohl prozentuale als auch monetäre Aussagen zu ermöglichen.

### 4.3 Datenvolumen und Datenqualität

Aus den vorhandenen Datensätzen können geschätzt **rund 8'000 bis 12'000 Trainings-Samples** generiert werden – das sind alle Verletzungen, für die sowohl ein Vor- als auch ein Nach-Marktwert verfügbar ist. Diese Datenmenge ist für Gradient-Boosting-Modelle ausreichend, ohne dass Overfitting-Risiken übermässig hoch werden.

## 5. Modellevaluation

Die Qualität des Modells wird mit anerkannten Regressions-Metriken bewertet:

| Metrik | Bedeutung | Erwarteter Wertebereich (Sport-Kontext) |
|---|---|---|
| **R² (Bestimmtheitsmass)** | Anteil der erklärten Varianz | 0.30 – 0.55 |
| **MAE (Mean Absolute Error)** | Mittlere absolute Abweichung in Prozentpunkten | 4 – 8 Prozentpunkte |
| **RMSE (Root Mean Squared Error)** | Gewichtete Abweichung, bestraft grosse Fehler | 6 – 12 Prozentpunkte |

Die Werte sind im Sport-Kontext realistisch, da Marktwertentwicklungen von vielen externen Faktoren beeinflusst werden (Trainerwechsel, Mannschaftserfolg, Transfergerüchte), die im Modell nicht abgebildet sind. Ein R² zwischen 0.30 und 0.50 gilt in der sportökonomischen Forschung bereits als guter Erklärungsgrad.

### 5.1 Validierungsverfahren

- **Train/Test-Split (80/20):** Aufteilung in Trainings- und Testdaten zur unverzerrten Evaluation
- **5-fache Kreuzvalidierung:** Stabilitätsprüfung des Modells über verschiedene Datenpartitionen
- **Random State fixiert:** Reproduzierbarkeit der Ergebnisse für die gesamte Projektgruppe

## 6. Erklärbarkeit der Vorhersagen (SHAP)

Eine entscheidende Anforderung für die managerielle Anwendung ist die **Erklärbarkeit einzelner Vorhersagen**. Hierfür werden **SHAP-Werte (Shapley Additive exPlanations)** eingesetzt. Pro Vorhersage zeigt SHAP, wie stark jedes Eingangsmerkmal zum Endresultat beigetragen hat.

**Beispiel-Aussage des Modells:**

> *Spieler X (32 Jahre, Centre-Back, Premier League, aktueller Marktwert 25 Mio. €, drei vorherige Verletzungen) erleidet einen Kreuzbandriss mit erwarteten 250 Ausfalltagen.*
>
> **Vorhergesagter Marktwert-Drop: −22.4 %** (95 %-Konfidenzintervall: −28 % bis −16 %)
>
> Top-Treiber dieser Vorhersage:
> - Verletzungstyp (Kreuzband): −10.1 %
> - Alter (32 Jahre): −7.8 %
> - Vorherige Verletzungen (3): −2.4 %
> - Position (Centre-Back): −1.6 %
> - Liga (Premier League): −0.5 %

Diese Aufschlüsselung ermöglicht es dem Sportdirektor oder CFO, die Vorhersage zu verstehen und in Vertragsverhandlungen oder Transferentscheidungen argumentativ zu nutzen.

## 7. Integration in das bestehende Dashboard

Das trainierte Modell wird als `joblib`-Datei (`.pkl`) gespeichert und im Streamlit-Dashboard im Tab «DDDM Entscheidungen» oder als neuer Tab «Verletzungs-Simulator» eingebunden.

**Geplante Benutzeroberfläche:**
- Eingabe-Widgets: Alter (Slider), Position (Dropdown), Verletzungstyp (Dropdown), Liga (Dropdown), aktueller Marktwert (Eingabefeld), vorherige Verletzungen (Slider)
- Ausgabe: Vorhergesagter Marktwertverlust in Prozent und Euro, Konfidenzintervall, SHAP-Waterfall-Plot zur Erklärung der Vorhersage
- Handlungsempfehlung: Automatisch generierte Empfehlung für Vertragsverhandlungen basierend auf dem Risiko-Niveau

## 8. DDDM-Bezug: Vom Datenpunkt zur Managemententscheidung

Das ML-Modell schliesst Schritt 4 des CPA-Frameworks («Informationen präsentieren / Entscheidungen treffen») konsequent ab:

| CPA-Schritt | Umsetzung |
|---|---|
| 1. Ziele definieren | Quantifizierung des finanziellen Verletzungsrisikos zur Entscheidungsunterstützung |
| 2. Daten sammeln | Verletzungs-, Spieler- und Marktwert-Daten aus Kaggle und Transfermarkt |
| 3. Daten analysieren | Deskriptive Analyse + Stratified Matching + ML-Vorhersagemodell |
| 4. Informationen präsentieren | Streamlit-Dashboard mit Risiko-Simulator als Entscheidungswerkzeug |

## 9. Technische Umsetzung – Bibliotheken und Werkzeuge

Sämtliche benötigten Bibliotheken sind Open Source und mit dem bestehenden Python-3.11-Setup kompatibel:

| Library | Funktion | Lizenz |
|---|---|---|
| `pandas` | Datenaufbereitung | BSD |
| `scikit-learn` | Lineare Regression als Baseline, Train/Test-Split, Metriken | BSD |
| `xgboost` | Gradient-Boosting-Hauptmodell | Apache 2.0 |
| `shap` | Erklärbarkeit der Vorhersagen | MIT |
| `joblib` | Speichern und Laden des trainierten Modells | BSD |

Die Erweiterung der Projekt-Dependencies erfolgt über:

```bash
uv add scikit-learn xgboost shap
```

## 10. Aufwandsschätzung

| Arbeitsschritt | Geschätzte Stunden |
|---|---|
| Datenaufbereitung (Feature-Engineering, Trainingsset bauen) | 2 – 3 h |
| Baseline-Modell (Lineare Regression) trainieren und evaluieren | 0.5 h |
| XGBoost-Modell trainieren, Hyperparameter-Tuning | 1 – 2 h |
| SHAP-Integration und Erklärbarkeit | 1 h |
| Streamlit-Integration im Dashboard | 1.5 – 2 h |
| Doku-Ergänzung und Vorbereitung Präsentation | 1 h |
| **Gesamt** | **7 – 9.5 h** |

Verteilt auf eine Gruppe von 5–6 Studierenden entspricht das einem individuellen Aufwand von **rund 1.5 Stunden pro Person**, sofern die Aufgaben sinnvoll aufgeteilt werden.

## 11. Erwartete Trainingsdauer (technisch)

Das eigentliche Modelltraining ist nicht zeitkritisch:

| Komponente | Dauer auf normalem Laptop |
|---|---|
| Lineare Regression (Baseline) | < 1 Sekunde |
| Random Forest | 5 – 15 Sekunden |
| XGBoost | 10 – 30 Sekunden |
| SHAP-Werte berechnen | 30 Sek – 2 Minuten |
| **Gesamter Notebook-Durchlauf** | **unter 5 Minuten** |

Das Modell wird einmal trainiert und anschliessend als Datei gespeichert. Im Dashboard sind die Vorhersagen dadurch praktisch verzögerungsfrei (< 100 ms pro Vorhersage).

## 12. Zusammenfassung

Das vorgeschlagene Machine-Learning-Modell ergänzt die deskriptive Analyse der Case Study um eine prädiktive, evidenzbasierte Komponente. Es übersetzt das in der bisherigen Auswertung sichtbare historische Muster («Verletzungen senken Marktwerte») in ein verallgemeinerbares Werkzeug, mit dem zukünftige Szenarien quantitativ bewertet werden können. Durch die Kombination aus etabliertem Algorithmus (XGBoost), transparenter Erklärbarkeit (SHAP) und direkter Einbindung ins Dashboard wird der CPA-Schritt 4 «Von Daten zu Entscheidungen» konsequent realisiert.

---

*Erstellt im Rahmen der BINA-Fallstudie FS2026 — Verletzungsanalyse europäischer Profifussball*
