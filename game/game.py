
basic_tiles = { #ints are only used for the special code
    "-":[0,-2],  #empty Space
    "#":[1,-1],  #wall
    " ":[2,-1],  #basic floor
    "*":[3, -2], #player
    "=":[9,-1],  #door, disappears if they have the key for it
    "<":[8,-1],  #keycard for the door
    "?":[7,-1],  #special interactable, do a function call
    "E":[0,-1],  #enemy type
    "^":[11,-1],  #staircase up
    "v":[12,-1],  #staircase down
    "@":[13,-1],  #starts from staircases
    "c":[21,-1],  #chest, refers to chest table
    "p":[22,-1]  #powerup
}

#  '#' 0 = concrete   1 = wood
#  ' ' 0 = concrete   1 = wood    2 = carpet   3 = tile
#  for staircases - -x-y x = level y = door  0001
#  each staircase must have a corresponding start on the given level
#        00 01 staircase, floor 00, there must be a start 01

"""
Used to change the second tuple value:
tile_type = tile[0]
tile_number = int(tile[1:])
"""
import os
import re

def decode_tiles(line):
    pattern = r".\d*"     # one character, followed by zero or more digits
    return re.findall(pattern, line.strip())

def make_grid(levelFile):
    grid = []
    valueGrid = []
    chestTable = []

    # --- FIX PATH ---
    # Level files are in ../assets/levels relative to game.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    level_path = os.path.join(script_dir, "..", "assets", "levels", levelFile)
    level_path = os.path.normpath(level_path)  # clean up any ../

    if not os.path.exists(level_path):
        raise FileNotFoundError(f"Level file not found at {level_path}")

    # --- Read level file ---
    with open(level_path, "r") as f:
        lineNum = 0
        width_line = f.readline().strip()
        height_line = f.readline().strip()

        width = int(width_line.split("=")[1])
        height = int(height_line.split("=")[1])
        for line in f:
            if lineNum < height:
                txtLine = line.strip()
                grid.append(decode_tiles(txtLine))
            else:
                txtLine = line.strip()
                chestTable.append(decode_tiles(txtLine))
            lineNum += 1

    # --- Build valueGrid ---
    for y in range(height):
        tmpgrid = []
        for x in range(width):
            tile = grid[y][x]
            key = tile[0]
            if key not in basic_tiles:
                tmpgrid.append((-1,-1))
                continue
            tile_values = basic_tiles[tile[0]][:]
            if tile_values[1] == -1:
                tile_values[1] = int(tile[1:])
            tmpgrid.append(tile_values)
        valueGrid.append(tmpgrid)

    for y in range(height):
        for x in range(width):
            print(grid[y][x][0], end = '')
        print()

    # --- Find player position ---
    player_pos = None
    for y in range(height):
        for x in range(width):
            if grid[y][x][0] == "*":
                player_pos = (x, y)
                # Replace the player marker with a floor tile so the sprite is drawn on top
                grid[y][x] = " "
                valueGrid[y][x] = basic_tiles[" "][:]
    if player_pos is None:
        # fallback
        player_pos = (28, 4)
        grid[1][1] = " "
        valueGrid[1][1] = basic_tiles[" "][:]

    return width, height, valueGrid, chestTable, grid, player_pos