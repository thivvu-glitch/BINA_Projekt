import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.visualizations import render_local_filters, open_soccermap_dialog, create_bodymap, body_categories, colorscale

def render(df, selected_leagues, selected_club_global, TOURNAMENT_OPTIONS, season_options):
    dialog_already_opened = False

    st.header("🦵 Körperregionanalyse")
    st.markdown("""
    **Welche Fragen werden dir in diesem Register beantwortet?**                
    - Welche Körperregionen sind am häufigsten von Verletzungen betroffen?
    - Welche anatomischen Schwachstellen zeigen sich je nach Liga oder Saison?
    - Welche Verletzungsarten zeigen die einzelnen Top-Ligen im Vergleich?
    - Durch einen Klick auf eine beliebige Körperregion: Welche Spielerpositionen sind am häufigsten von Verletzungen dieser Körperregion betroffen?
             
    **Für wen?**
    - Medizinisches Personal
    - Physiotherapeuten
    - Sportmediziner
    - Forscher

    **Was sieht man?**
    - Verletzungen nach Körperregion (Muskeln, Knie, Knöchel, etc.)
    - Anatomische Schwachpunkte pro Liga für gezielte Präventions- und Rehabilitationsmassnahmen
    - Häufigste Verletzungstypen nach Körperteil
    - Vergleich der Verletzungsmuster während den Grossturnieren (z. B. WM/EM) und regulären Saisons
    """)
    st.divider()

    st.subheader("🧍‍♂️ Interaktive Körperkarte")
    st.markdown("Analysiere die Verletzungen der Spieler anhand der Körperregionen.")
    st.info("""
    💡 **Kurzanleitung zur interaktiven Körperkarte:**
    - **Details anzeigen:** Klicke auf ein beliebiges Körperteil (z. B. Knie) am Körper oder auf einen Punkt in der Legende. Es öffnet sich ein neues Fenster mit einem Spielfeld und einer Tabelle, die dir exakt zeigt, auf welchen Spielerpositionen diese Verletzung am häufigsten auftritt.
    - **Fenster schliessen:** Klicke einfach auf das 'X' oben rechts oder neben das Fenster, um zur Bodymap-Übersicht zurückzukehren.
    - **Auswahl aufheben:** Wenn du ein Körperteil angeklickt hast, bleibt es markiert. Mache einfach einen **Doppelklick** auf einen leeren Bereich neben dem Strichmännchen, um die Auswahl aufzuheben und die Karte zurückzusetzen.
    """)

    body_df = render_local_filters("bodymap", df, TOURNAMENT_OPTIONS, season_options)

    if body_df.empty:
        st.info("Keine Daten für die aktuelle Saison-Auswahl in der Körperkarte verfügbar.")

    if not body_df.empty:
        league_body_df = body_df[body_df["injury_category"].isin(body_categories)].copy()
        if league_body_df.empty:
            global_min, global_max = 0, 1
        else:
            league_cat_counts = league_body_df.groupby(['league', 'injury_category']).size().reset_index(name='count')
            if league_cat_counts.empty:
                global_min, global_max = 0, 1
            else:
                global_min, global_max = league_cat_counts['count'].min(), league_cat_counts['count'].max()
    
        if not league_body_df.empty:
            fig_cbar = go.Figure(go.Scatter(
                x=[-10], y=[-10], mode="markers",
                marker=dict(
                    size=0,
                    color=[global_min, global_max],
                    colorscale=colorscale,
                    cmin=global_min, cmax=global_max,
                    showscale=True,
                    colorbar=dict(
                        title="Anzahl Verletzungen",
                        orientation="h",
                        thickness=15,
                        yanchor="bottom", y=0,
                        xanchor="center", x=0.5,
                        len=0.6,
                        outlinewidth=0,
                    )
                ),
                hoverinfo="none"
            ))
            fig_cbar.update_layout(
                height=100, 
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(visible=False, range=[0, 1]), yaxis=dict(visible=False, range=[0, 1]),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_cbar, use_container_width=True, key="bodymap_colorbar")
    
        if len(selected_leagues) == 1:
            league = selected_leagues[0]
            title = f"Verletzungshotspots nach Körperzone – {league}"
            if selected_club_global != "Alle Clubs":
                title += f" ({selected_club_global})"
            st.markdown(f"**{title}**")
            fig = create_bodymap(body_df, global_min, global_max)
            if fig:
                event = st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, on_select="rerun", key=f"bodymap_single_{league}")
                current_sel = event.selection["points"][0]["customdata"][5] if event and event.selection.get("points") else None
                prev_sel = st.session_state.previous_selections.get(f"bodymap_single_{league}")
                if current_sel and current_sel != prev_sel and not dialog_already_opened:
                    dialog_already_opened = True
                    st.session_state.previous_selections[f"bodymap_single_{league}"] = current_sel
                    open_soccermap_dialog(league, current_sel, body_df)
                elif not current_sel:
                    st.session_state.previous_selections[f"bodymap_single_{league}"] = None
            else:
                st.info("Keine Daten für die aktuelle Auswahl in der Körperkarte verfügbar.")
        else:
            st.markdown("**Vergleich der Ligen:** Jede Karte zeigt die Verletzungsmuster nach Körperzone einer Liga.")
            league_pairs = [selected_leagues[i:i+2] for i in range(0, len(selected_leagues), 2)]
            for pair in league_pairs:
                cols = st.columns(2)
                for idx, league in enumerate(pair):
                    with cols[idx]:
                        league_df = body_df[body_df['league'] == league]
                        title = f"Verletzungshotspots – {league}"
                        if selected_club_global != "Alle Clubs":
                            title += f" ({selected_club_global})"
                        st.markdown(f"<div style='text-align: center;'><b>{title}</b></div>", unsafe_allow_html=True)
                        fig = create_bodymap(league_df, global_min, global_max)
                        if fig:
                            event = st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, on_select="rerun", key=f"bodymap_multi_{league}")
                            current_sel = event.selection["points"][0]["customdata"][5] if event and event.selection.get("points") else None
                            prev_sel = st.session_state.previous_selections.get(f"bodymap_multi_{league}")
                            if current_sel and current_sel != prev_sel and not dialog_already_opened:
                                dialog_already_opened = True
                                st.session_state.previous_selections[f"bodymap_multi_{league}"] = current_sel
                                open_soccermap_dialog(league, current_sel, body_df)
                            elif not current_sel:
                                st.session_state.previous_selections[f"bodymap_multi_{league}"] = None
                        else:
                            st.info(f"Keine Daten für {league} verfügbar.")

