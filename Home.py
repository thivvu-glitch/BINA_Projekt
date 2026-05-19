import streamlit as st

st.set_page_config(page_title="Home", page_icon="🏠")

st.title("Europäische Fussballverletzungen (2020-2025)")

st.sidebar.success("Wähle eine Seite aus dem Menü")

st.markdown("""
Die Fallstudie wurde im Rahmen des Moduls BINA im FS2026 des Masterstudiengangs Wirtschaftsinformatik realisiert. Das Projektteam besteht aus folgenden Mitgliedern: Aron Halef, Michael Huwiler, Thivvirthan Krishnakumar, Kevin Kurinjirappalli, Sarankan Maheswaran und Alessandra Schneller. 
            
Dieses Business Intelligence Dashboard ermöglicht die Analyse von Verletzungsmustern im europäischen Profifussball und 
basiert auf der **CPA Management Accounting Guideline** für datengesteuerte Entscheidungen.
""")

# Hero Image
# st.image("assets/Homescreen_pic.png", use_container_width=True)
# st.caption("Quelle: KI generiert")

st.markdown("---")

st.markdown("### Projekt-Dokumentation")
st.write("In der Dokumentation findest du die ausführliche Beschreibung der BINA-Fallstudie sowie die Umsetzung der vier Schritte der CPA Management Accounting Guideline.")
st.page_link("pages/1_Dokumentation.py", label="Dokumentation öffnen")

st.markdown("---")

st.markdown("### Analyse-Dashboard")
st.write("Das Dashboard ist in verschiedene Bereiche unterteilt, um unterschiedliche Fragestellungen zu beantworten:")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Zeitvergleich & Trends")
    st.write("Strategische Analyse des Turnier-Impacts (WM/EM) und Belastungssteuerung über die Saisons.")
    st.page_link("pages/2_Dashboard.py", label="Zu Zeitvergleich & Trends", query_params={"tab": "Zeitvergleich & Trends"}, icon="📈")
    
    st.divider()
    
    st.markdown("#### Spielfeldanalyse")
    st.write("Visualisierung der Verletzungshäufigkeit basierend auf der Spielerposition auf dem Spielfeld.")
    st.page_link("pages/2_Dashboard.py", label="Zu Spielfeldanalyse", query_params={"tab": "Spielfeldanalyse"}, icon="⚽")
    
    st.divider()
    
    st.markdown("#### Körperrgionanalyse")
    st.write("Anatomische Darstellung der am häufigsten betroffenen Körperregionen.")
    st.page_link("pages/2_Dashboard.py", label="Zur Körperregionanalyse", query_params={"tab": "Körperregionanalyse"}, icon="🦵")

with col2:
    st.markdown("#### Club Analyse")
    st.write("Nutzt Daten für fundierte 'Data-Driven Decision Making' Prozesse im Vereinsmanagement.")
    st.page_link("pages/2_Dashboard.py", label="Zu Clubanalyse", query_params={"tab": "Clubanalyse"}, icon="💼")
    
    st.divider()
    
    st.markdown("#### Marktwert & Risiko")
    st.write("Analyse des wirtschaftlichen Risikos und des Zusammenhangs zwischen Verletzungen und Marktwert.")
    st.page_link("pages/2_Dashboard.py", label="Zur Marktwert-Analyse", query_params={"tab": "Marktwert- & Risiko-Analyse"}, icon="💸")
    
    st.divider()
    
    st.markdown("#### Verletzungssimulator")
    st.write("Simuliere verschiedene Verletzungsszenarien und analysiere deren wirtschaftliche Auswirkungen.")
    st.page_link("pages/2_Dashboard.py", label="Zur Verletzungssimulation", query_params={"tab": "Verletzungssimulator"}, icon="🔮")