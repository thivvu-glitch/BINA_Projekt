import streamlit as st
import plotly.graph_objects as go
from utils.visualizations import render_local_filters, open_bodymap_dialog, create_soccer_map

def render(df, selected_leagues, selected_club_global, TOURNAMENT_OPTIONS, season_options):
    dialog_already_opened = False
    st.header("⚽ Spielfeldanalyse")
    st.markdown("""
    **Welche Fragen werden dir in diesem Register beantwortet?**
    - In welchen Spielpositionen verletzen sich Spieler pro Liga am meisten?
    - Durch einen Klick auf eine beliebige Spielerposition: Welche Arten von Verletzungen ergeben sich pro Position?
                
    **Für wen?**
    - Trainer
    - Athletik-Trainer
    - Positionscoaches
    - Scouts
    
    **Was sieht man?**
    - Interaktive Feldpositionen-Visualisierung (virtueller Fussballplatz)
    - Verletzungshäufigkeit nach Spielerposition
    - Positions-spezifische Verletzungsmuster
    - Betroffene Spieler pro Position
    - Strategische Insights für Aufstellung und Spielerrotation
    - Vergleich der Verletzungsmuster während den Grossturnieren (z. B. WM/EM) und regulären Saisons
    """)
    st.divider()
    
    st.subheader("🥅 Interaktives Spielfeld")
    st.markdown("Analysiere die Verletzungen der Spieler nach Position in den einzelnen Clubs.")
    st.info("""
    💡 **Kurzanleitung zur interaktiven Karte:**
    - **Details anzeigen:** Klicke auf eine beliebige Position (z. B. Centre-Back) auf dem Spielfeld. Es öffnet sich ein neues Fenster mit einer Körperkarte und Tabelle, die dir genau zeigt, welche Körperteile bei der ausgewählten Position am häufigsten verletzt wurden.
    - **Fenster schliessen:** Klicke einfach auf das 'X' oben rechts oder neben das Fenster, um zur Spielfeld-Übersicht zurückzukehren.
    - **Auswahl aufheben:** Wenn du eine Position angeklickt hast, bleibt sie markiert. Mache einfach einen **Doppelklick** auf den leeren grünen Rasen, um die Auswahl aufzuheben und die Karte zurückzusetzen.
    """)
    
    maps_df = render_local_filters("maps", df, TOURNAMENT_OPTIONS, season_options)


    # Compute global min and max for the color scale across all displayed data
    position_coords_keys = [
        "Goalkeeper", "Left-Back", "Centre-Back", "Right-Back", 
        "Defensive Midfield", "Central Midfield", "Attacking Midfield", 
        "Midfielder", "Left Midfield", "Right Midfield", 
        "Left Winger", "Right Winger", "Second Striker", "Forward"
    ]
    global_counts = maps_df[maps_df['player_position'].isin(position_coords_keys)].groupby(['league', 'player_position']).size().reset_index(name='count')
    if global_counts.empty:
        global_min, global_max = 0, 1
    else:
        global_min, global_max = global_counts['count'].min(), global_counts['count'].max()

    # Create a dummy horizontal colorbar
    if not global_counts.empty:
        fig_cbar = go.Figure(go.Scatter(
            x=[-10], y=[-10], mode="markers",
            marker=dict(
                size=0,
                color=[global_min, global_max],
                colorscale=[
                    [0.0, "#FEE2E2"],
                    [0.25, "#FCA5A5"],
                    [0.5, "#F87171"],
                    [0.75, "#DC2626"],
                    [1.0, "#7F1D1D"]
                ],
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
        st.plotly_chart(fig_cbar, use_container_width=True)

    if len(selected_leagues) == 1:
        # Single league - show one soccer map
        league = selected_leagues[0]
        title = f"Spielerpositionen mit Verletzungshäufung – {league}"
        if selected_club_global != "Alle Clubs":
            title += f" ({selected_club_global})"
        
        st.markdown(f"**{title}**")
        fig = create_soccer_map(maps_df, global_min, global_max)
        if fig:
            event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key=f"soccer_map_single_{league}")
            current_sel = event.selection["points"][0]["customdata"][0] if event and event.selection.get("points") else None
            prev_sel = st.session_state.previous_selections.get(f"soccer_map_single_{league}")
            if current_sel and current_sel != prev_sel and not dialog_already_opened:
                dialog_already_opened = True
                st.session_state.previous_selections[f"soccer_map_single_{league}"] = current_sel
                open_bodymap_dialog(league, current_sel, maps_df)
            elif not current_sel:
                st.session_state.previous_selections[f"soccer_map_single_{league}"] = None
        else:
            st.info("Keine Daten für die aktuelle Auswahl in der Kartenansicht verfügbar.")
    
    else:
        # Multiple leagues - show one soccer map per league, max 2 per row
        st.markdown("**Vergleich der Ligen:** Jede Karte zeigt die Verletzungsmuster nach Position einer Liga.")
        
        # Group leagues into pairs for display
        league_pairs = [selected_leagues[i:i+2] for i in range(0, len(selected_leagues), 2)]
        
        for pair in league_pairs:
            cols = st.columns(2)
            for idx, league in enumerate(pair):
                with cols[idx]:
                    league_df = maps_df[maps_df['league'] == league]
                    title = f"Spielerpositionen – {league}"
                    if selected_club_global != "Alle Clubs":
                        title += f" ({selected_club_global})"
                    
                    st.markdown(f"<div style='text-align: center;'><b>{title}</b></div>", unsafe_allow_html=True)
                    fig = create_soccer_map(league_df, global_min, global_max)
                    if fig:
                        event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", key=f"soccer_map_multi_{league}")
                        current_sel = event.selection["points"][0]["customdata"][0] if event and event.selection.get("points") else None
                        prev_sel = st.session_state.previous_selections.get(f"soccer_map_multi_{league}")
                        if current_sel and current_sel != prev_sel and not dialog_already_opened:
                            dialog_already_opened = True
                            st.session_state.previous_selections[f"soccer_map_multi_{league}"] = current_sel
                            open_bodymap_dialog(league, current_sel, maps_df)
                        elif not current_sel:
                            st.session_state.previous_selections[f"soccer_map_multi_{league}"] = None
                    else:
                        st.info(f"Keine Daten für {league} verfügbar.")

