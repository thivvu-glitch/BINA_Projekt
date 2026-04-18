import streamlit as st

st.set_page_config(page_title="Home", page_icon="🏠")

st.title("Europäische Fussballverletzungen (2020-2025)")

st.sidebar.success("Wähle eine Seite aus dem Menü")

st.markdown("""
Dieses Business Intelligence Dashboard ermöglicht die Analyse von Verletzungsmustern im europäischen Profifussball und 
basiert auf der **CPA Management Accounting Guideline** für datengesteuerte Entscheidungen.
""")

# Hero Image
st.image("picture/Homescreen_pic.png", use_container_width=True)
st.caption("Quelle: ki generiert")

st.markdown("---")

st.markdown("### Projekt-Dokumentation")
st.write("In der Dokumentation findest du die ausführliche Beschreibung der BINA-Fallstudie sowie die Umsetzung der vier Schritte der CPA Management Accounting Guideline.")
st.page_link("pages/1_Dokumentation.py", label="Dokumentation öffnen")

st.markdown("---")

st.markdown("### Analyse-Dashboard")
st.write("Das Dashboard ist in verschiedene Bereiche unterteilt, um unterschiedliche Fragestellungen zu beantworten:")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Übersicht")
    st.write("Ein schneller Überblick über die wichtigsten KPIs und den Vergleich der europäischen Top-Ligen.")
    st.page_link("pages/2_Dashboard.py", label="Zur Übersicht", query_params={"tab": "Übersicht"})
    
    st.divider()
    
    st.markdown("#### Verletzungsvergleich")
    st.write("Detaillierte Analyse und Vergleich spezifischer Verletzungsarten über alle Ligen hinweg.")
    st.page_link("pages/2_Dashboard.py", label="Zum Verletzungsvergleich", query_params={"tab": "Verletzungsvergleich"})
    
    st.divider()
    
    st.markdown("#### Zeit & Liga")
    st.write("Analyse von saisonalen Trends, monatlichen Mustern und der zeitlichen Entwicklung.")
    st.page_link("pages/2_Dashboard.py", label="ZuZeit & Liga", query_params={"tab": "Zeit & Liga"})
    
    st.divider()
    
    st.markdown("#### Tabellen")
    st.write("Vollständige, filterbare Datenbank aller erfassten Verletzungsfälle für Detailanalysen.")
    st.page_link("pages/2_Dashboard.py", label="Zu den Tabellen", query_params={"tab": "Tabellen"})

with col2:
    st.markdown("#### Karten")
    st.write("Visualisierung der Verletzungshäufigkeit basierend auf der Spielerposition auf dem Spielfeld.")
    st.page_link("pages/2_Dashboard.py", label="Zu den Karten", query_params={"tab": "Karten"})
    
    st.divider()
    
    st.markdown("#### Bodymap")
    st.write("Anatomische Darstellung der am häufigsten betroffenen Körperregionen.")
    st.page_link("pages/2_Dashboard.py", label="Zur Bodymap", query_params={"tab": "Bodymap"})
    
    st.divider()
    
    st.markdown("#### DDDM Entscheidungen")
    st.write("Nutzt Daten für fundierte 'Data-Driven Decision Making' Prozesse im Vereinsmanagement.")
    st.page_link("pages/2_Dashboard.py", label="Zu DDDM-Entscheidungen", query_params={"tab": "DDDM Entscheidungen"})
    
    st.divider()
    
    st.markdown("#### Marktwert & Risiko")
    st.write("Analyse des wirtschaftlichen Risikos und des Zusammenhangs zwischen Verletzungen und Marktwert.")
    st.page_link("pages/2_Dashboard.py", label="Zur Marktwert-Analyse", query_params={"tab": "Marktwert & Risiko-Analyse"})