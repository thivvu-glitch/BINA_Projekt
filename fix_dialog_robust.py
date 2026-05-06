with open('pages/2_Dashboard.py', 'r') as f:
    content = f.read()

# Add previous_selections to session state
setup_code = """
if "previous_selections" not in st.session_state:
    st.session_state.previous_selections = {}
dialog_already_opened = False
"""
content = content.replace("dialog_already_opened = False\n", setup_code)

def replace_logic(key_var, event_get, customdata_index, open_dialog_func, args):
    old_code = f"""if event and event.selection.get("points") and not dialog_already_opened:
                            dialog_already_opened = True
                            pos = event.selection["points"][0]["customdata"][{customdata_index}]
                            {open_dialog_func}({args})"""
    
    # We will use regex to replace with proper indentation
    pass

# Let's just use regex to replace the exact blocks
import re

# Single Soccer
content = re.sub(
    r'if event and event\.selection\.get\("points"\) and not dialog_already_opened:\s+dialog_already_opened = True\s+pos = event\.selection\["points"\]\[0\]\["customdata"\]\[0\]\s+open_bodymap_dialog\(league, pos, maps_df\)',
    r'''current_sel = event.selection["points"][0]["customdata"][0] if event and event.selection.get("points") else None
            prev_sel = st.session_state.previous_selections.get(f"soccer_map_single_{league}")
            if current_sel and current_sel != prev_sel and not dialog_already_opened:
                dialog_already_opened = True
                st.session_state.previous_selections[f"soccer_map_single_{league}"] = current_sel
                open_bodymap_dialog(league, current_sel, maps_df)
            elif not current_sel:
                st.session_state.previous_selections[f"soccer_map_single_{league}"] = None''',
    content
)

# Multi Soccer
content = re.sub(
    r'if event and event\.selection\.get\("points"\) and not dialog_already_opened:\s+dialog_already_opened = True\s+pos = event\.selection\["points"\]\[0\]\["customdata"\]\[0\]\s+open_bodymap_dialog\(league, pos, maps_df\)',
    r'''current_sel = event.selection["points"][0]["customdata"][0] if event and event.selection.get("points") else None
                            prev_sel = st.session_state.previous_selections.get(f"soccer_map_multi_{league}")
                            if current_sel and current_sel != prev_sel and not dialog_already_opened:
                                dialog_already_opened = True
                                st.session_state.previous_selections[f"soccer_map_multi_{league}"] = current_sel
                                open_bodymap_dialog(league, current_sel, maps_df)
                            elif not current_sel:
                                st.session_state.previous_selections[f"soccer_map_multi_{league}"] = None''',
    content
)

# Single Bodymap
content = re.sub(
    r'if event and event\.selection\.get\("points"\) and not dialog_already_opened:\s+dialog_already_opened = True\s+body_part = event\.selection\["points"\]\[0\]\["customdata"\]\[5\]\s+open_soccermap_dialog\(league, body_part, body_df\)',
    r'''current_sel = event.selection["points"][0]["customdata"][5] if event and event.selection.get("points") else None
                    prev_sel = st.session_state.previous_selections.get(f"bodymap_single_{league}")
                    if current_sel and current_sel != prev_sel and not dialog_already_opened:
                        dialog_already_opened = True
                        st.session_state.previous_selections[f"bodymap_single_{league}"] = current_sel
                        open_soccermap_dialog(league, current_sel, body_df)
                    elif not current_sel:
                        st.session_state.previous_selections[f"bodymap_single_{league}"] = None''',
    content
)

# Multi Bodymap
content = re.sub(
    r'if event and event\.selection\.get\("points"\) and not dialog_already_opened:\s+dialog_already_opened = True\s+body_part = event\.selection\["points"\]\[0\]\["customdata"\]\[5\]\s+open_soccermap_dialog\(league, body_part, body_df\)',
    r'''current_sel = event.selection["points"][0]["customdata"][5] if event and event.selection.get("points") else None
                                prev_sel = st.session_state.previous_selections.get(f"bodymap_multi_{league}")
                                if current_sel and current_sel != prev_sel and not dialog_already_opened:
                                    dialog_already_opened = True
                                    st.session_state.previous_selections[f"bodymap_multi_{league}"] = current_sel
                                    open_soccermap_dialog(league, current_sel, body_df)
                                elif not current_sel:
                                    st.session_state.previous_selections[f"bodymap_multi_{league}"] = None''',
    content
)

with open('pages/2_Dashboard.py', 'w') as f:
    f.write(content)
print("Robust fix applied.")
