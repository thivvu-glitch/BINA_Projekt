import re

with open('pages/2_Dashboard.py', 'r') as f:
    lines = f.readlines()

# Let's find the exact indices
map_func_start = next(i for i, l in enumerate(lines) if "def create_soccer_map(data_df, global_min, global_max):" in l)
map_func_end = next(i for i, l in enumerate(lines[map_func_start:]) if "return fig" in l) + map_func_start + 1

bodymap_config_start = next(i for i, l in enumerate(lines) if "# Konfiguration" in l) - 1
bodymap_func_end = next(i for i, l in enumerate(lines[bodymap_config_start:]) if "return fig" in l) + bodymap_config_start + 1

# Extract blocks
map_func_lines = lines[map_func_start:map_func_end]
bodymap_lines = lines[bodymap_config_start:bodymap_func_end]

# Remove the extracted blocks from their original places
# Note: we must do it from bottom to top to preserve indices
del lines[bodymap_config_start:bodymap_func_end]
del lines[map_func_start:map_func_end]

# Dedent the bodymap lines because they were under "else:"
def dedent(lines_arr, amount=8):
    return [l[amount:] if l.startswith(' ' * amount) else l for l in lines_arr]

map_func_lines = dedent(map_func_lines, 4)
bodymap_lines = dedent(bodymap_lines, 8)

# Find where to insert (before "with tap_maps:")
insert_idx = next(i for i, l in enumerate(lines) if "with tap_maps:" in l)

# Create Dialog Functions
dialogs = """
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

@st.dialog("Spielfeld Details", width="large")
def open_soccermap_dialog(league, body_part, df):
    # To translate the body part back to readable text if needed
    st.subheader(f"Positionen mit Verletzung: {body_part} ({league})")
    
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

"""

# Insert all
lines.insert(insert_idx, "\n# --- VISUALIZATION FUNCTIONS FOR DIALOGS ---\n")
for l in reversed(map_func_lines): lines.insert(insert_idx + 1, l)
for l in reversed(bodymap_lines): lines.insert(insert_idx + 1, l)
for l in reversed(dialogs.split('\n')): lines.insert(insert_idx + 1, l + '\n')

with open('pages/2_Dashboard.py', 'w') as f:
    f.writelines(lines)
print("Refactoring complete.")
