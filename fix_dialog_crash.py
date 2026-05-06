with open('pages/2_Dashboard.py', 'r') as f:
    content = f.read()

# Add dialog_already_opened = False before tap_maps
if "dialog_already_opened = False" not in content:
    content = content.replace("with tap_maps:", "dialog_already_opened = False\nwith tap_maps:")

# Replace in single soccer map
content = content.replace(
    'if event and event.selection.get("points"):\n                pos = event.selection["points"][0]["customdata"][0]\n                open_bodymap_dialog(league, pos, maps_df)',
    'if event and event.selection.get("points") and not dialog_already_opened:\n                dialog_already_opened = True\n                pos = event.selection["points"][0]["customdata"][0]\n                open_bodymap_dialog(league, pos, maps_df)'
)

# Replace in multi soccer map
content = content.replace(
    'if event and event.selection.get("points"):\n                            pos = event.selection["points"][0]["customdata"][0]\n                            open_bodymap_dialog(league, pos, maps_df)',
    'if event and event.selection.get("points") and not dialog_already_opened:\n                            dialog_already_opened = True\n                            pos = event.selection["points"][0]["customdata"][0]\n                            open_bodymap_dialog(league, pos, maps_df)'
)

# Replace in single bodymap
content = content.replace(
    'if event and event.selection.get("points"):\n                    body_part = event.selection["points"][0]["customdata"][5]\n                    open_soccermap_dialog(league, body_part, body_df)',
    'if event and event.selection.get("points") and not dialog_already_opened:\n                    dialog_already_opened = True\n                    body_part = event.selection["points"][0]["customdata"][5]\n                    open_soccermap_dialog(league, body_part, body_df)'
)

# Replace in multi bodymap
content = content.replace(
    'if event and event.selection.get("points"):\n                                body_part = event.selection["points"][0]["customdata"][5]\n                                open_soccermap_dialog(league, body_part, body_df)',
    'if event and event.selection.get("points") and not dialog_already_opened:\n                                dialog_already_opened = True\n                                body_part = event.selection["points"][0]["customdata"][5]\n                                open_soccermap_dialog(league, body_part, body_df)'
)

with open('pages/2_Dashboard.py', 'w') as f:
    f.write(content)
print("Dialog fix applied.")
