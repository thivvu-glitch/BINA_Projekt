import streamlit as st
import pandas as pd
def render(df, val_df, players_info_df, player_options_map):
    st.header("🔮 Verletzungs-Simulator: Marktwert-Auswirkung")
    st.markdown("""
    **Welche Fragen werden dir in diesem Register beantwortet?**                
    - Wie stark würde sich eine hypothetische Verletzung auf den Marktwert eines Spielers auswirken?
    - Welche Verletzungsarten verursachen den grössten finanziellen Schaden?
    - Wie verändert sich der Marktwert je nach Ausfallzeit?
                    
    **Für wen?**
    - Sportdirektor
    - Scouts
    - CFO / Club-Manager
                
    **Was sieht man?**
    - **Machine Learning-Prognose:** Vorhersage des Marktwertverlusta bei einer hypothetischen Verletzung
    - **Spielerspezifische Simulation:** Basierend auf Spielerdaten (Alter, Position, Liga, Historie)
    - **Generischer Simulator:** Manuelle Parametereingabe für theoretische Szenarien
    - **SHAP-Explainability:** Verständnis, welche Faktoren die Vorhersage treiben
    - **Vertragsverhandlung:** Finanzielle Risikobewertung für Vertragsverhandlungen
    """)
    st.divider()

    import sys
    import os
    import matplotlib.pyplot as plt
    import shap
        
    try:
        from machine_learning.ml_predict import predict_market_change
        
        # --- Gemeinsame Ergebnis-Anzeige Funktion ---
        def display_prediction_results(res, player_label=None):
            """Zeigt die Vorhersage-Ergebnisse, Handlungsempfehlung und SHAP-Plot an."""
            st.divider()
            if player_label:
                st.subheader(f"📊 Prognoseergebnis für {player_label}")
            else:
                st.subheader("📊 Prognoseergebnis")
            
            k_col1, k_col2, k_col3 = st.columns(3)
            drop_pct = res['drop_pct']
            
            k_col1.metric("Erwartete Marktwertänderung", f"{drop_pct:.1f} %", delta=f"{drop_pct:.1f}%", delta_color="normal")
            k_col2.metric("Finanzieller Verlust", f"{res['loss_eur']/1e6:.2f} Mio. €", delta=f"{res['loss_eur']/1e6:.2f} Mio. €", delta_color="normal")
            k_col3.metric("Neuer Marktwert", f"€ {res['new_mv']/1e6:.2f} Mio.")
            
            st.markdown("### 💡 Handlungsempfehlung")
            if drop_pct > -5.0:
                st.success("🟢 **Geringes Risiko:** Der zu erwartende Marktwertverlust ist minimal. Keine akuten vertraglichen Massnahmen zwingend erforderlich.")
            elif drop_pct > -15.0:
                st.warning("🟡 **Mittleres Risiko:** Spürbarer Einfluss auf den Marktwert. Bei Vertragsverhandlungen sollte die Verletzungshistorie berücksichtigt werden.")
            else:
                st.error("🔴 **Hohes Risiko:** Signifikanter Marktwertverlust! Es wird empfohlen, Leistungsklauseln in zukünftige Verträge aufzunehmen und einen Notfallplan für diese Position zu prüfen.")
                
            st.markdown("### 🧠 Erklärbarkeit der Vorhersage (SHAP)")
            
            tab_local, tab_global = st.tabs(["Lokal (Waterfall Plot)", "Global (Beeswarm Plot)"])
            
            with tab_local:
                st.write("**Individuelle Vorhersage:** Dieser Plot zeigt, wie jedes einzelne Merkmal (blau = Wertsteigernd/weniger Verlust, rot = Wertmindernd/mehr Verlust) die **aktuelle** Vorhersage des XGBoost-Modells gebildet hat.")
                fig, ax = plt.subplots(figsize=(10, 6))
                shap.plots.waterfall(res['shap_values'][0], show=False)
                st.pyplot(fig, clear_figure=True)
                
            with tab_global:
                st.write("**Allgemeines Modellverhalten:** Dieser Plot zeigt die globale Wichtigkeit und den Einfluss der Features über eine grosse Stichprobe des Modells hinweg. Jeder Punkt ist eine historische Verletzung. Rote Punkte stehen für hohe Feature-Werte (z.B. hohes Alter), blaue für niedrige.")
                
                from machine_learning.ml_predict import get_global_shap_data
                global_shap_values = get_global_shap_data()
                
                if global_shap_values is not None:
                    fig2, ax2 = plt.subplots(figsize=(10, 6))
                    shap.plots.beeswarm(global_shap_values, show=False)
                    st.pyplot(fig2, clear_figure=True)
                else:
                    st.info("Globale SHAP-Werte wurden nicht im Modell gespeichert. Bitte das Modell mit dem aktualisierten Skript neu trainieren.")
        
        # --- Zwei Sub-Tabs ---
        sim_tab_player, sim_tab_generic = st.tabs(["🔍 Spieler-Suche", "⚙️ Generischer Simulator"])
        
        # ===========================
        # SUB-TAB 1: SPIELER-SUCHE
        # ===========================
        with sim_tab_player:
            st.markdown("""
            > Suche einen konkreten Spieler aus dem Datensatz. Seine Daten werden automatisch übernommen. 
            > Du wählst nur noch die **hypothetische Verletzung** aus.
            """)
            def on_player_select():
                """Callback: Aktualisiert Session State nur wenn Widget sich ändert"""
                selection = st.session_state.player_search_widget
                st.session_state['risk_selected_player'] = selection[0] if selection else None
            # Spieler-Suche – gleicher Stil wie im Marktwert-Tab (Multiselect)
            player_options_local_sim = sorted(player_options_map.keys())
            sel_sim_p = st.multiselect(
                "👤 Spieler suchen",
                options=player_options_local_sim,
                default=[],
                max_selections=1,
                help="Wähle einen Spieler aus, um seinen Steckbrief und eine Verletzungs-Simulation zu sehen.",
                key="sim_player_multiselect",
                on_change=on_player_select
                )   

            
            sim_selected_player_id = player_options_map.get(sel_sim_p[0]) if sel_sim_p else None
            
            if sim_selected_player_id is not None:
                # Spieler-Daten aus dem Datensatz laden
                player_injuries = df[df['player_id'] == sim_selected_player_id].sort_values('injury_from_parsed')
                player_info = players_info_df[players_info_df['player_id'] == sim_selected_player_id]
                
                if not player_injuries.empty:
                    # Spieler-Profil anzeigen
                    p_name = player_injuries['player_name'].iloc[0]
                    p_age = int(player_injuries['player_age'].iloc[-1]) if pd.notna(player_injuries['player_age'].iloc[-1]) else 25
                    p_position = player_injuries['player_position'].iloc[0] if pd.notna(player_injuries['player_position'].iloc[0]) else "Unknown"
                    p_league = player_injuries['league'].iloc[-1] if pd.notna(player_injuries['league'].iloc[-1]) else "Unknown"
                    p_club = player_injuries['club'].iloc[-1] if pd.notna(player_injuries['club'].iloc[-1]) else "Unbekannt"
                    
                    # Marktwert: neuester aus val_df oder aus dem Injury-Datensatz
                    p_val_data = val_df[val_df['player_id'] == sim_selected_player_id].sort_values('date')
                    if not p_val_data.empty and pd.notna(p_val_data.iloc[-1]['market_value_in_eur']):
                        p_mv = int(p_val_data.iloc[-1]['market_value_in_eur'])
                    elif not player_info.empty and 'market_value_in_eur' in player_info.columns and pd.notna(player_info.iloc[0]['market_value_in_eur']):
                        p_mv = int(player_info.iloc[0]['market_value_in_eur'])
                    else:
                        p_mv = 1000000  # Fallback
                    
                    # Verletzungshistorie berechnen
                    p_prev_injuries = len(player_injuries)
                    p_prev_days = int(player_injuries['Days'].fillna(0).sum())
                    
                    # --- Spieler-Steckbrief (identisch zum Marktwert-Tab) ---
                    st.markdown(f"### 👤 Spieler-Steckbrief: {p_name}")
                    
                    if not player_info.empty:
                        p_data = player_info.iloc[0]
                        
                        prof_col1, prof_col2 = st.columns([0.8, 3.2])
                        
                        with prof_col1:
                            # Spieler-Bild von Transfermarkt
                            if pd.notna(p_data.get('image_url', None)):
                                st.image(p_data['image_url'], use_container_width=True)
                            else:
                                st.info("Kein Bild verfügbar")
                        
                        with prof_col2:
                            stat_col1, stat_col2 = st.columns(2)
                            
                            with stat_col1:
                                st.write(f"**Nationalität:** {p_data['country_of_citizenship']}" if pd.notna(p_data.get('country_of_citizenship')) else "**Nationalität:** Unbekannt")
                                st.write(f"**Geburtsdatum:** {pd.to_datetime(p_data['date_of_birth']).strftime('%d.%m.%Y')}" if pd.notna(p_data.get('date_of_birth')) else "**Geburtsdatum:** Unbekannt")
                                st.write(f"**Position:** {p_data['position']}" if pd.notna(p_data.get('position')) else f"**Position:** {p_position}")
                                st.write(f"**Starker Fuss:** {p_data['foot'].capitalize()}" if pd.notna(p_data.get('foot')) else "**Starker Fuss:** Unbekannt")
                                
                                # Club Logo
                                c_name = p_data.get('current_club_name', p_club)
                                c_id = p_data.get('current_club_id', None)
                                if pd.notna(c_id):
                                    logo_url = f"https://tmssl.akamaized.net/images/wappen/medium/{int(c_id)}.png"
                                    st.markdown(f"**Aktueller Club:** {c_name}")
                                    st.image(logo_url, width=60)
                                else:
                                    st.write(f"**Aktueller Club:** {c_name}")
                            
                            with stat_col2:
                                st.write(f"**Grösse:** {int(p_data['height_in_cm'])} cm" if pd.notna(p_data.get('height_in_cm')) else "**Grösse:** Unbekannt")
                                st.write(f"**Länderspiele:** {int(p_data['international_caps'])}" if pd.notna(p_data.get('international_caps')) else "**Länderspiele:** 0")
                                st.write(f"**Länderspieltore:** {int(p_data['international_goals'])}" if pd.notna(p_data.get('international_goals')) else "**Länderspieltore:** 0")
                                st.write(f"**Bisherige Verletzungen:** {p_prev_injuries}")
                                st.write(f"**Kumulierte Ausfalltage:** {p_prev_days}")
                            
                            st.divider()
                            m1, m2 = st.columns(2)
                            m1.metric("Aktueller Marktwert", f"€{p_mv:,.0f}".replace(",", "."))
                            if pd.notna(p_data.get('highest_market_value_in_eur')):
                                m2.metric("Höchster Marktwert", f"€{p_data['highest_market_value_in_eur']:,.0f}".replace(",", "."))
                    else:
                        # Fallback: Einfache Karte, wenn keine players_info vorhanden
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                                    padding: 20px; border-radius: 12px; margin-bottom: 20px; color: white;">
                            <h3 style="margin: 0 0 12px 0; color: #f8fafc;">⚽ {p_name}</h3>
                            <p>Position: {p_position} | Liga: {p_league} | Alter: {p_age} | Marktwert: €{p_mv:,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
                    
                    # Nur noch Verletzung und Ausfalltage eingeben
                    st.markdown("#### 🔮 Was-wäre-wenn: Verletzungsszenario simulieren")
                    sim_p_col1, sim_p_col2 = st.columns(2)
                    with sim_p_col1:
                        sim_p_category = st.selectbox("Verletzungskategorie", df['injury_category'].dropna().unique().tolist(), key="sim_p_cat")
                    with sim_p_col2:
                        sim_p_days = st.slider("Erwartete Ausfalltage", 1, 400, 30, key="sim_p_days")
                    
                    if st.button("🔮 Vorhersage für diesen Spieler berechnen", use_container_width=True, type="primary", key="sim_p_btn"):
                        with st.spinner(f"Berechne Prognose für {p_name}..."):
                            res = predict_market_change(
                                age=p_age,
                                position=p_position,
                                injury_category=sim_p_category,
                                days_out=sim_p_days,
                                current_mv=float(p_mv),
                                league=p_league,
                                prev_injuries=p_prev_injuries,
                                total_prev_days=p_prev_days
                            )
                        display_prediction_results(res, player_label=p_name)
                else:
                    st.warning("Keine Verletzungsdaten für diesen Spieler gefunden.")
        
        # ===========================
        # SUB-TAB 2: GENERISCHER SIMULATOR
        # ===========================
        with sim_tab_generic:
            st.markdown("""
            > Stelle die Parameter manuell ein, um ein hypothetisches Spielerprofil zu simulieren.
            > Ideal für allgemeine Risikobewertungen oder Transfer-Due-Diligence.
            """)
            
            col_in1, col_in2, col_in3 = st.columns(3)
            with col_in1:
                sim_age = st.slider("Alter", 16, 40, 25, key="gen_age")
                sim_position = st.selectbox("Position", df['player_position'].dropna().unique().tolist(), key="gen_pos")
                sim_league = st.selectbox("Liga", df['league'].dropna().unique().tolist(), key="gen_league")
            with col_in2:
                sim_category = st.selectbox("Verletzungskategorie", df['injury_category'].dropna().unique().tolist(), key="gen_cat")
                sim_days = st.slider("Erwartete Ausfalltage", 1, 400, 30, key="gen_days")
                sim_mv = st.number_input("Aktueller Marktwert (€)", min_value=100000, max_value=250000000, value=25000000, step=1000000, key="gen_mv")
            with col_in3:
                sim_prev_inj = st.slider("Anzahl vorheriger Verletzungen", 0, 10, 0, key="gen_prev_inj")
                sim_prev_days = st.slider("Kumulierte Ausfalltage bisher", 0, 1000, 0, key="gen_prev_days")
                
            if st.button("🔮 Vorhersage berechnen", use_container_width=True, type="primary", key="gen_btn"):
                with st.spinner("Berechne Machine-Learning-Prognose..."):
                    res = predict_market_change(
                        age=sim_age,
                        position=sim_position,
                        injury_category=sim_category,
                        days_out=sim_days,
                        current_mv=sim_mv,
                        league=sim_league,
                        prev_injuries=sim_prev_inj,
                        total_prev_days=sim_prev_days
                    )
                display_prediction_results(res)
            
    except Exception as e:
        st.error(f"Fehler beim Laden des ML-Modells. Bitte stelle sicher, dass 'machine_learning/train_model.py' erfolgreich ausgeführt wurde. Details: {e}")