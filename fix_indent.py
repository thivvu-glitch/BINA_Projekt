with open('pages/2_Dashboard.py', 'r') as f:
    lines = f.readlines()

# Line 1116 is index 1115
lines[1115] = lines[1115].lstrip() # 0 spaces for def create_bodymap

# Lines 1117 to 1347 are indices 1116 to 1346
for i in range(1116, 1347):
    # Add 4 spaces
    lines[i] = "    " + lines[i]

with open('pages/2_Dashboard.py', 'w') as f:
    f.writelines(lines)
print("Indentation fixed.")
