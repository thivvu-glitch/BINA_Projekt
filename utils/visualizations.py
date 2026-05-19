import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.data_loader import load_tournament_players

def render_local_filters(tab_prefix, df, TOURNAMENT_OPTIONS, season_options):
    st.info("**Kurzanleitung:** Nutze den Turnierfilter, um gezielt die Verletzungen einer WM/EM-Kohorte (z. B. WM 2022) zu analysieren oder wähle 'Alle Spieler' für eine allgemeine Liga-Übersicht. Über den Saison-Filter kannst du den Zeitraum anpassen, um z. B. die Belastung während einer Turniersaison im Vergleich zu anderen Jahren zu untersuchen. Alle Grafiken passen sich automatisch deiner Auswahl an.", icon="💡")
    st.markdown("#### ⚙️ Filter (Turnier & Saison)")
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            t_filter = st.selectbox("Turnierfilter", TOURNAMENT_OPTIONS, index=0, key=f"{tab_prefix}_tournament")
        with col2:
            s_filter = st.multiselect("Saisons", season_options, default=season_options, key=f"{tab_prefix}_seasons")
            
    local_df = df.copy()
    if s_filter:
        local_df = local_df[local_df['Season'].isin(s_filter)]
        
    if "Alle Spieler" not in t_filter:
        e20, w22, e24 = load_tournament_players()
        if "EURO 2020" in t_filter:
            local_df = local_df[local_df['player_id'].isin(e20)]
        elif "WM 2022" in t_filter:
            local_df = local_df[local_df['player_id'].isin(w22)]
        elif "EURO 2024" in t_filter:
            local_df = local_df[local_df['player_id'].isin(e24)]
        elif "WM und EM" in t_filter:
            local_df = local_df[local_df['player_id'].isin(e20.union(w22).union(e24))]
        elif "Keine Turnierteilnahme" in t_filter:
            all_t = e20.union(w22).union(e24)
            local_df = local_df[~local_df['player_id'].isin(all_t)]
            
    return local_df


# --- VISUALIZATION FUNCTIONS FOR DIALOGS ---

@st.dialog("Bodymap Details", width="large")
def open_bodymap_dialog(league, position, df):
    st.subheader(f"Verletzungen für: {position} ({league})")
    df_filtered = df[(df['league'] == league) & (df['player_position'] == position)]
    if df_filtered.empty:
        st.info("Keine Daten vorhanden.")
        return
        
    c1, c2 = st.columns([1, 1])
    with c1:
        # We need a body_df for create_bodymap. create_bodymap uses injury_category
        fig = create_bodymap(df_filtered, 0, len(df_filtered))
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.write("Verletzungs-Details")
        display_df = df_filtered[['player_name', 'club', 'Injury', 'Days']].copy()
        display_df.columns = ['Spieler', 'Verein', 'Verletzung', 'Ausfalltage']
        display_df = display_df.sort_values('Ausfalltage', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

@st.dialog("Spielfeld-Details", width="large")
def open_soccermap_dialog(league, body_part, df):
    # To translate the body part back to readable text if needed
    st.subheader(f"Positionen mit Verletzung in der {league}: {body_part}")
    
    # Check if the clicked part was from the legend
    # if body_part in legend_category_mapping values ... wait, body_categories vs legend
    # Let's filter df where injury_category == body_part
    df_filtered = df[(df['league'] == league) & (df['injury_category'] == body_part)]
    if df_filtered.empty:
        st.info("Keine Daten vorhanden.")
        return
        
    c1, c2 = st.columns([1, 1])
    with c1:
        fig = create_soccer_map(df_filtered, 0, len(df_filtered))
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.write("Verletzungs-Details")
        display_df = df_filtered[['player_name', 'club', 'Injury', 'Days', 'player_position']].copy()
        display_df.columns = ['Spieler', 'Verein', 'Verletzung', 'Ausfalltage', 'Position']
        display_df = display_df.sort_values('Ausfalltage', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)


# -----------------------
# Konfiguration
# -----------------------
position_coords = {
    "Head": (50, 124),
    "Neck": (50, 115),
    "Shoulder": (34.5, 108),
    "Chest/Ribs": (50, 106),
    "Back/Spine": (50, 96),
    "Abdomen/Core": (50, 82),
    "Hip/Groin": (50, 68),
    "Upper Arm": (31.5, 94),
    "Elbow": (31.5, 81.5),
    "Forearm": (31.5, 70),
    "Hand/Finger": (31.5, 60),
    "Thigh": (44.5, 56),
    "Knee": (44.5, 43.5),
    "Lower Leg": (44.5, 30),
    "Ankle": (50, 14),
    "Foot/Toe": (40.5, 15),
}

bodypart_display_mapping = {
    "Head": "Kopf",
    "Neck": "Nacken",
    "Shoulder": "Schulter",
    "Chest/Ribs": "Brust / Rippen",
    "Back/Spine": "Rücken / Wirbelsäule",
    "Abdomen/Core": "Bauch / Rumpf",
    "Hip/Groin": "Hüfte / Leiste",
    "Upper Arm": "Oberarm",
    "Elbow": "Ellbogen",
    "Forearm": "Unterarm",
    "Hand/Finger": "Hand / Finger",
    "Thigh": "Oberschenkel",
    "Knee": "Knie",
    "Lower Leg": "Unterschenkel",
    "Ankle": "Knöchel",
    "Foot/Toe": "Fuss / Zehen",
}

legend_category_mapping = {
    "Muskeln": "Muscle",
    "Knochen": "Bone",
    "Bänder": "Ligament",
    "Operation": "Surgery",
    "Krankheit": "Illness",
    "Leichte Verletzung": "Minor",
    "Nicht verletzungsbedingt": "Non-injury",
}

legend_items = [
    "Muskeln",
    "Knochen",
    "Bänder",
    "Operation",
    "Krankheit",
    "Leichte Verletzung",
    "Nicht verletzungsbedingt",
]

category_colors = {
    "Muskeln": "#DC2626",
    "Knochen": "#7C3AED",
    "Bänder": "#2563EB",
    "Surgery": "#EA580C",
    "Illness": "#DB2777",
    "Minor": "#F59E0B",
    "Non-Injury": "#64748B",
}

body_categories = set(position_coords.keys())
legend_categories = set(legend_category_mapping.values())

colorscale = [
    [0.0, "#FEE2E2"],
    [0.25, "#FCA5A5"],
    [0.5, "#F87171"],
    [0.75, "#DC2626"],
    [1.0, "#7F1D1D"],
]

def aggregate_injuries(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["injury_category", "injury_count", "player_name", "injury_type", "total_days"])

    return (
        df.groupby("injury_category", as_index=False)
        .agg(
            injury_count=("injury_category", "size"),
            player_name=("player_name", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))),
            injury_type=("Injury", lambda x: ", ".join(sorted(set(x.dropna().astype(str))))),
            total_days=("Days", "sum")
        )
    )

def get_text_color(value: int, vmin: int, vmax: int) -> str:
    if vmax == vmin:
        return "#FFFFFF"
    threshold = vmin + (vmax - vmin) * 0.55
    return "#FFFFFF" if value >= threshold else "#111827"

def translate_bodypart(category: str) -> str:
    return bodypart_display_mapping.get(category, category)

def format_hover_list_limited(value: str, items_per_line: int = 3, max_items: int = 8) -> str:
    if not value:
        return "Keine Angaben"

    items = [item.strip() for item in str(value).split(",") if item.strip()]
    if not items:
        return "Keine Angaben"

    shown_items = items[:max_items]
    lines = []

    for i in range(0, len(shown_items), items_per_line):
        lines.append(", ".join(shown_items[i:i + items_per_line]))

    result = "<br>".join(lines)

    if len(items) > max_items:
        result += f"<br><i>… und {len(items) - max_items} weitere</i>"

    return result

def create_bodymap(data_df, global_min, global_max):
    body_df = data_df[data_df["injury_category"].isin(body_categories)].copy()
    body_counts = aggregate_injuries(body_df)
    
    if body_counts.empty:
        return None
    
    body_counts["x"] = body_counts["injury_category"].map(lambda cat: position_coords[cat][0])
    body_counts["y"] = body_counts["injury_category"].map(lambda cat: position_coords[cat][1])
    body_counts["display_category"] = body_counts["injury_category"].apply(translate_bodypart)
    body_counts["player_name_hover"] = body_counts["player_name"].apply(
        lambda x: format_hover_list_limited(x, items_per_line=3, max_items=8)
    )
    body_counts["injury_type_hover"] = body_counts["injury_type"].apply(
        lambda x: format_hover_list_limited(x, items_per_line=2, max_items=6)
    )
    
    legend_df = data_df[data_df["injury_category"].isin(legend_categories)].copy()
    legend_counts = aggregate_injuries(legend_df)
    
    legend_counts["display_category"] = legend_counts["injury_category"].apply(
        lambda x: next((k for k, v in legend_category_mapping.items() if v == x), x)
    )
    legend_counts["player_name_hover"] = legend_counts["player_name"].apply(
        lambda x: format_hover_list_limited(x, items_per_line=3, max_items=8)
    )
    legend_counts["injury_type_hover"] = legend_counts["injury_type"].apply(
        lambda x: format_hover_list_limited(x, items_per_line=2, max_items=6)
    )
    
    min_count = global_min
    max_count = global_max
    
    body_counts["text_color"] = body_counts["injury_count"].apply(
        lambda value: get_text_color(value, min_count, max_count)
    )
    
    fig = go.Figure()
    
    # Layout
    fig.update_layout(
        height=600,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=120, t=20, b=20),
        font=dict(
            family="Arial, sans-serif",
            color="#334155"
        ),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#CBD5E1",
            font=dict(
                color="#0F172A",
                size=13,
                family="Arial, sans-serif"
            ),
            align="left"
        ),
        xaxis=dict(
            visible=False,
            range=[0, 100],
            fixedrange=True
        ),
        yaxis=dict(
            visible=False,
            range=[0, 140],
            scaleanchor="x",
            scaleratio=1,
            fixedrange=True
        )
    )
    
    body_line = dict(color="#94A3B8", width=1.8)
    body_fill = "#E9EEF5"
    joint_fill = "#F8FAFC"
    
    shapes = [
        dict(type="circle", x0=40, y0=114, x1=60, y1=134, line=body_line, fillcolor=joint_fill, layer="below"),
        dict(type="rect", x0=46, y0=109, x1=54, y1=114, line=dict(color="rgba(0,0,0,0)"), fillcolor=body_fill, layer="below"),
        dict(type="path", path="M 35 108 Q 34 92 35 72 L 65 72 Q 66 92 65 108 Q 58 114 50 114 Q 42 114 35 108 Z", line=body_line, fillcolor=body_fill, layer="below"),
        dict(type="path", path="M 35 108 Q 29 101 28 94 L 28 60 Q 28 57 31 57 L 35 57 L 35 106 Z", line=body_line, fillcolor="#F1F5F9", layer="below"),
        dict(type="path", path="M 65 108 Q 71 101 72 94 L 72 60 Q 72 57 69 57 L 65 57 L 65 106 Z", line=body_line, fillcolor="#F1F5F9", layer="below"),
        dict(type="circle", x0=28, y0=77, x1=35, y1=86, line=body_line, fillcolor=joint_fill, layer="below"),
        dict(type="circle", x0=65, y0=77, x1=72, y1=86, line=body_line, fillcolor=joint_fill, layer="below"),
        dict(type="path", path="M 40 72 L 60 72 L 58 64 L 42 64 Z", line=body_line, fillcolor="#D7DEE8", layer="below"),
        dict(type="path", path="M 42 64 L 49 64 L 49 20 L 40 20 L 40 58 Q 40 62 42 64 Z", line=body_line, fillcolor="#F1F5F9", layer="below"),
        dict(type="path", path="M 51 64 L 58 64 L 60 58 L 60 20 L 51 20 Z", line=body_line, fillcolor="#F1F5F9", layer="below"),
        dict(type="circle", x0=40, y0=39, x1=49, y1=48, line=body_line, fillcolor=joint_fill, layer="below"),
        dict(type="circle", x0=51, y0=39, x1=60, y1=48, line=body_line, fillcolor=joint_fill, layer="below"),
        dict(type="path", path="M 38 20 L 49 20 L 49 10 L 36 10 L 36 16 Q 36 20 38 20 Z", line=body_line, fillcolor="#E2E8F0", layer="below"),
        dict(type="path", path="M 51 20 L 62 20 Q 64 20 64 18 L 64 10 L 51 10 Z", line=body_line, fillcolor="#E2E8F0", layer="below"),
    ]
    fig.update_layout(shapes=shapes)
    

    legend_x = 85
    legend_y_start = 112
    gap = 10
    
    fig.add_annotation(
        x=legend_x,
        y=legend_y_start + 10,
        text="<b>Kategorien</b>",
        showarrow=False,
        xanchor="left",
        font=dict(size=14, color="#475569")
    )
    
    visible_index = 0
    
    for label in legend_items:
        mapped_category = legend_category_mapping[label]
        row = legend_counts[legend_counts["injury_category"] == mapped_category]
    
        if row.empty:
            continue
    
        count = int(row.iloc[0]["injury_count"])
        if count <= 0:
            continue
    
        y = legend_y_start - visible_index * gap
        visible_index += 1
    
        player_name_hover = row.iloc[0]["player_name_hover"]
        injury_type_hover = row.iloc[0]["injury_type_hover"]
        text_color = get_text_color(count, min_count, max_count)
    
        total_days = int(row.iloc[0].get("total_days", 0))
    
        customdata = [[label, count, player_name_hover, injury_type_hover, total_days, mapped_category]]
    
        fig.add_trace(go.Scatter(
            x=[legend_x + 2],
            y=[y],
            mode="markers+text",
            text=[count],
            textposition="middle center",
            customdata=customdata,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Anzahl: %{customdata[1]}<br>"
                "Ausfalltage insgesamt: %{customdata[4]}"
                "<extra></extra>"
            ),
            marker=dict(
                size=30,
                color=[count],
                colorscale=colorscale,
                cmin=min_count,
                cmax=max_count,
                line=dict(color="#FFFFFF", width=2.5),
                opacity=0.97,
                showscale=False
            ),
            textfont=dict(
                size=12,
                color="#000000",
                family="Arial, sans-serif"
            ),
            showlegend=False
        ))
    
        fig.add_annotation(
            x=legend_x + 6,
            y=y,
            text=label,
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            font=dict(size=12, color="#475569")
        )
    
    hover_custom = body_counts[[
        "display_category",
        "injury_count",
        "player_name_hover",
        "injury_type_hover",
        "total_days",
        "injury_category"
    ]]
    
    fig.add_trace(go.Scatter(
        x=body_counts["x"],
        y=body_counts["y"],
        mode="markers+text",
        text=body_counts["injury_count"],
        textposition="middle center",
        customdata=hover_custom,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Anzahl: %{customdata[1]}<br>"
            "Ausfalltage insgesamt: %{customdata[4]:.0f}"
            "<extra></extra>"
        ),
        marker=dict(
            size=30,                    
            color=body_counts["injury_count"],
            colorscale=colorscale,
            cmin=min_count,
            cmax=max_count,
            line=dict(color="#FFFFFF", width=2.5),
            showscale=False,
            opacity=0.97
        ),
        textfont=dict(
            size=12,
            color="#000000",
            family="Arial, sans-serif"
        ),
        showlegend=False
    ))
    
    fig.add_annotation(
        x=50,
        y=2.5,
        text="Dunklere Marker zeigen häufiger registrierte Verletzungen",
        showarrow=False,
        font=dict(size=12, color="#64748B"),
        xanchor="center",
    )
    return fig
def create_soccer_map(data_df, global_min, global_max):
    if data_df.empty:
        return None

    position_coords = {
        "Goalkeeper": (5, 40),

        "Left-Back": (20, 65),
        "Centre-Back": (20, 40),
        "Right-Back": (20, 15),

        "Defensive Midfield": (37, 40),
        "Central Midfield": (55, 40),
        "Attacking Midfield": (73, 40),
        "Midfielder": (55, 52),

        "Left Midfield": (52, 65),
        "Right Midfield": (52, 15),

        "Left Winger": (85, 68),
        "Right Winger": (85, 12),

        "Second Striker": (92, 40),
        "Forward": (105, 40)
    }

    club_df = data_df[data_df['player_position'].isin(position_coords.keys())].copy()

    if club_df.empty:
        return None

    injury_counts = (
        club_df.groupby("player_position")
        .size()
        .reset_index(name="injury_count")
    )

    injury_counts['x'] = injury_counts['player_position'].map(lambda p: position_coords.get(str(p), (None, None))[0])
    injury_counts['y'] = injury_counts['player_position'].map(lambda p: position_coords.get(str(p), (None, None))[1])

    # Hover-details
    details = (
        club_df.groupby("player_position")
        .agg({
            "player_name": lambda x: ", ".join(sorted(set(map(str, x)))),
            "Injury": lambda x: ", ".join(sorted(set(map(str, x)))),
            "Days": "sum"
        })
        .reset_index()
    )

    injury_counts = injury_counts.merge(details, on="player_position", how="left")

    fig = go.Figure()

    fig.update_layout(
        height=450,
        plot_bgcolor="#6aa84f",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(
            family="Arial, sans-serif",
            color="#334155"
        ),
        xaxis=dict(
            visible=False,
            range=[0, 100],
            fixedrange=True
        ),
        yaxis=dict(
            visible=False,
            range=[0, 140],
            scaleanchor="x",
            scaleratio=1,
            fixedrange=True
        )
    )

    shapes = [
        dict(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color="white", width=3), layer="below"),  # soccer field
        dict(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color="white", width=3), layer="below"),  # halfway line
        dict(type="circle", x0=50, y0=30, x1=70, y1=50, line=dict(color="white", width=3), layer="below"),  # center circle
        dict(type="circle", x0=59, y0=39, x1=61, y1=41, line=dict(color="white", width=2), fillcolor="white", layer="below"),  # center mark

        dict(type="rect", x0=0, y0=18, x1=18, y1=62, line=dict(color="white", width=3), layer="below"),  # goal area left
        dict(type="rect", x0=102, y0=18, x1=120, y1=62, line=dict(color="white", width=3), layer="below"),  # goal area right

        dict(type="rect", x0=0, y0=30, x1=6, y1=50, line=dict(color="white", width=3), layer="below"),  # penalty area left
        dict(type="rect", x0=114, y0=30, x1=120, y1=50, line=dict(color="white", width=3), layer="below"),  # penalty area right

        dict(type="circle", x0=10, y0=39, x1=12, y1=41, line=dict(color="white", width=2), fillcolor="white", layer="below"),  # penalty mark left
        dict(type="circle", x0=108, y0=39, x1=110, y1=41, line=dict(color="white", width=2), fillcolor="white", layer="below"),  # penalty mark right

        dict(type="path", path="M 18,32 Q 25,40 18,48", line_color="white", layer="below"),  # penalty arc left
        dict(type="path", path="M 102,32 Q 95,40 102,48", line_color="white", layer="below"),  # penalty arc right

        dict(type="path", path="M 0,76 Q 4,76 4,80", line_color="white", layer="below"),  # corner arc top left
        dict(type="path", path="M 0,4 Q 4,4 4,0", line_color="white", layer="below"),  # corner arc down left
        dict(type="path", path="M 120,76 Q 116,76 116,80", line_color="white", layer="below"),  # corner arc top right
        dict(type="path", path="M 120,4 Q 116,4 116,0", line_color="white", layer="below"),  # corner arc bottom right
    ]

    fig.update_layout(shapes=shapes)

    # Marker-Styling
    min_count = global_min
    max_count = global_max

    fig.add_trace(go.Scatter(
        x=injury_counts['x'],
        y=injury_counts['y'],
        mode="markers+text",
        text=injury_counts['injury_count'],
        textposition="middle center",
        textfont=dict(
            color="black",
            size=16,
            weight="bold"
        ),
        marker=dict(
            size=36,
            color=injury_counts["injury_count"],
            colorscale=[
                [0.0, "#FEE2E2"],
                [0.25, "#FCA5A5"],
                [0.5, "#F87171"],
                [0.75, "#DC2626"],
                [1.0, "#7F1D1D"]
            ],
            cmin=min_count,
            cmax=max_count,
            line=dict(color="#FFFFFF", width=2.5),
            showscale=False,
            opacity=0.97
        ),
        customdata=injury_counts[['player_position', 'injury_count', 'player_name', 'Injury', 'Days']],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Anzahl Verletzungen: %{customdata[1]}<br>"
            "Ausfalltage insgesamt: %{customdata[4]:.0f}<extra></extra>"
        )
    ))

    # Labels
    for _, row in injury_counts.iterrows():
        fig.add_annotation(
            x=row['x'],
            y=row['y'] - 6,
            text=row['player_position'],
            showarrow=False,
            font=dict(size=11, color="black")
        )

    fig.update_xaxes(visible=False, range=[0, 120])
    fig.update_yaxes(visible=False, range=[0, 80], scaleanchor="x", scaleratio=1)

    return fig

