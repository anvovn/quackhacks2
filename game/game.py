
basic_tiles = { #ints are only used for the special code
    "-":[0,-2],  #empty Space
    "#":[1,-2],  #wall
    " ":[2,-2],  #basic floor
    "*":[3, -2], # player
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
    chestTable =[#((value it changes, how much it changes by),(...)...)
    ]

    width = 0
    height = 0

    script_dir = os.path.dirname(os.path.abspath(__file__))
    level_path = os.path.join(script_dir, "..", "assets", "levels", levelFile)

    with open(level_path, "r") as f:
        lineNum = 0
        txtLine = ""
        txtList = []
        width_line = f.readline().strip()
        height_line = f.readline().strip()

        width = int(width_line.split("=")[1])
        height = int(height_line.split("=")[1])
        for line in f:
            if (lineNum < height):
                txtLine = line.strip()
                grid.append(decode_tiles(txtLine))
            if (lineNum > height):
                txtLine = line.strip()
                chestTable.append(decode_tiles(txtLine))
            lineNum += 1
    """
    #make grid
    for y in range(height):
        tmpgrid = []
        for x in range(width):
            if(x == 0 or x == width-1 or y == 0 or y == height-2):
                tmpgrid.append("#")
            else:
                tmpgrid.append("-")
        grid.append(tmpgrid)
    """
    
    test_row = ["p21","c9","^1","v1","@1","E1","?1","<1","=1"]
    for x in range(width):
        #print(x,len(test_row))
        if x < len(test_row):
            pass

    #print grid
    for y in range(height):
        for x in range(width):
            print(grid[y][x], end = '')
        print()

    for y in range(height):
        tmpgrid = []
        for x in range(width): 
            tile = grid[y][x]
            key = tile[0]
            if key not in basic_tiles:
                tmpgrid.append((-1,-1))
                continue
            tile_values = basic_tiles[tile[0]]
            if (tile_values[1] == -1):
                tile_values[1] = int(tile[1:])
            tmpgrid.append(tile_values)
        valueGrid.append(tmpgrid)
    grid[5][5] = "*"
        # Find player
    player_pos = None
    for y in range(height):
        for x in range(width):
            if grid[y][x][0] == "*":   # tile begins with player symbol
                player_pos = (x, y)
                
    return (width, height, valueGrid, chestTable, grid, player_pos)