import os
import re
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from typing import List, Dict, Tuple, Any

# --- Game Constants and Tile Definitions ---
basic_tiles: Dict[str, Tuple[int, int]] = {
    "-":[0,-2],  # empty Space
    "#":[1,-1],  # wall
    " ":[2,-1],  # basic floor
    "*":[3, -2], # player
    "=":[9,-1],  # door, disappears if they have the key for it
    "<":[8,-1],  # keycard for the door
    "?":[7,-1],  # special interactable, do a function call
    "E":[0,-1],  # enemy type
    "^":[11,-1], # staircase up
    "v":[12,-1], # staircase down
    "@":[13,-1], # starts from staircases
    "c":[21,-1], # chest, refers to chest table
    "p":[22,-1]  # powerup
}

# Mock level content to simulate reading from assets/levels/level_0.txt
MOCK_LEVEL_CONTENT = """
width=10
height=10
##########
#* #
# ?      #
# #######
# < = c  #
# E # p  #
# v #    #
# ^ #    #
#        #
##########
ChestTableData
chest_0:itemA,itemB
"""

# IMPORTANT CHANGE: Specify template_folder and static_folder paths relative to server.py
# Since server.py is in 'game/', templates/ and static/ are in the parent directory.

# Use absolute paths relative to the current working directory
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# ADD: Serve assets as static files
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_dir = os.path.join(BASE_DIR, "assets")
    return send_from_directory(assets_dir, filename)

# ... existing GAME_STATE ...

@app.route('/')
def mp():
    return render_template('index.html')

# ADD: Routes for other HTML pages
@app.route('/tutorial.html')
def tutorial():
    return render_template('tutorial.html')

@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/settings.html')
def settings():
    return render_template('settings.html')

@app.route('/credits.html')
def credits():
    return render_template('credits.html')
            
GAME_STATE: Dict[str, Any] = {}

# --- Utility Functions (decode_tiles, make_grid, etc., remain unchanged) ---

def decode_tiles(line: str) -> List[str]:
    """Decodes a line of tile characters and optional numbers."""
    pattern = r".\d*"
    return re.findall(pattern, line.strip())

def make_grid(level_content: str) -> Tuple[int, int, List[List[Tuple[int, int]]], List[List[str]], List[List[str]], Tuple[int, int]]:
    """
    Parses the level content string into game data structures.
    """
    grid: List[List[str]] = []
    valueGrid: List[List[Tuple[int, int]]] = []
    chestTable: List[List[str]] = []
    lines = level_content.strip().split('\n')

    width = int(lines[0].split("=")[1])
    height = int(lines[1].split("=")[1])

    for i in range(2, 2 + height):
        txtLine = lines[i].strip()
        grid.append(decode_tiles(txtLine))

    for i in range(2 + height + 1, len(lines)):
        txtLine = lines[i].strip()
        chestTable.append(decode_tiles(txtLine))


    # --- Build valueGrid ---
    for y in range(height):
        tmpgrid = []
        for x in range(width):
            tile = grid[y][x]
            key = tile[0]
            if key not in basic_tiles:
                tmpgrid.append((-1,-1))
                continue

            tile_values = list(basic_tiles[key])
            if tile_values[1] == -1 and len(tile) > 1 and tile[1:].isdigit():
                tile_values[1] = int(tile[1:])
            elif tile_values[1] == -1:
                 tile_values[1] = 0

            tmpgrid.append(tuple(tile_values))
        valueGrid.append(tmpgrid)

    # --- Find player position ---
    player_pos: Tuple[int, int] = (1, 1)
    found = False
    for y in range(height):
        for x in range(width):
            if grid[y][x][0] == "*":
                player_pos = (x, y)
                found = True
                break
        if found:
            break

    simple_grid = [[t[0] for t in row] for row in grid]

    return width, height, valueGrid, chestTable, simple_grid, player_pos

# --- Game Logic Functions (move_player logic remains the same) ---

def move_player(grid: List[List[str]], value_grid: List[List[Tuple[int, int]]], player_pos: Tuple[int, int], direction: str) -> Tuple[Tuple[int, int], str]:
    x, y = player_pos
    message = ""

    offsets = { "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0) }
    if direction not in offsets: return player_pos, "Invalid direction."
    dx, dy = offsets[direction]
    nx, ny = x + dx, y + dy

    if ny < 0 or ny >= len(grid) or nx < 0 or nx >= len(grid[0]): return player_pos, "Movement blocked by map boundary."

    tile_char = grid[ny][nx]
    basic_solid = {"#", "E"}
    if tile_char in basic_solid or tile_char == "=":
        if tile_char == "=": return player_pos, "Door blocked — you need a key!"
        return player_pos, "Movement blocked by a solid object."

    new_pos = (nx, ny)

    if tile_char == "<": message = "Picked up a key!"
    elif tile_char == "^": message = "Stairs going UP!"
    elif tile_char == "v": message = "Stairs going DOWN!"
    elif tile_char == "c": message = "Opened chest! (Need to implement chest lookup)"
    elif tile_char == "p": message = "Picked up a powerup!"
    elif tile_char == " ": message = "Moved onto a floor space."
    else: message = "Moved into an empty space."

    grid[y][x] = "-"
    value_grid[y][x] = basic_tiles["-"][:]
    grid[ny][nx] = "*"
    value_grid[ny][nx] = basic_tiles["*"][:]

    return new_pos, message

# --- Flask Routes ---

@app.route('/game.html')
def game_page():
    """Serves the main game client HTML file (game.html)."""
    # We use game.html for the playable client
    return render_template('game.html')


@app.route('/api/start_game', methods=['POST'])
def start_game():
    # ... (start_game logic remains the same)
    try:
        width, height, value_grid, chest_table, grid, player_pos = make_grid(MOCK_LEVEL_CONTENT)

        GAME_STATE['grid'] = grid
        GAME_STATE['value_grid'] = value_grid
        GAME_STATE['player_pos'] = player_pos
        GAME_STATE['width'] = width
        GAME_STATE['height'] = height
        GAME_STATE['message'] = "Game started successfully."

        return jsonify({
            "success": True,
            "grid": grid,
            "value_grid": value_grid,
            "player_pos": player_pos,
            "message": GAME_STATE['message'],
            "width": width,
            "height": height
        })
    except Exception as e:
        app.logger.error(f"Error starting game: {e}")
        return jsonify({"success": False, "message": f"Server error during game start: {str(e)}"}), 500

@app.route('/api/move', methods=['POST'])
def handle_move():
    # ... (handle_move logic remains the same)
    if 'grid' not in GAME_STATE:
        return jsonify({"success": False, "message": "Game not initialized. Call /api/start_game first."}), 400

    data = request.get_json()
    direction = data.get('direction', '').lower()

    if direction not in ['w', 'a', 's', 'd']:
        return jsonify({"success": False, "message": "Invalid direction provided. Use 'w', 'a', 's', or 'd'."}), 400

    current_pos = GAME_STATE['player_pos']
    grid = GAME_STATE['grid']
    value_grid = GAME_STATE['value_grid']

    new_pos, message = move_player(grid, value_grid, current_pos, direction)

    GAME_STATE['player_pos'] = new_pos
    GAME_STATE['message'] = message

    return jsonify({
        "success": True,
        "grid": grid,
        "player_pos": new_pos,
        "message": message,
        "width": GAME_STATE['width'],
        "height": GAME_STATE['height']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)