
tiles = [
    '0':0  #empty Space
    '#':1  #wall
    ' ':2  #basic floor
    "=#":#9  #door, disappears if they have the key for it
    "<#":#8  #keycard for the door
    "?#":17  #special interactable, do a function call
    "E#":#0  #enemy type
    "^#":#11  #staircase up
    "v#":#12  #staircase down 
    "@#":#13  #starts from staircases
    "c#":#21
    "p#":#22

]
chestTable =
[
"M250,HP10,MHP10",
]

print("Start")
grid = []

width = 15
height = 5

for x in range(width):
    tmpgrid = []
    for y in range(height):
        tmpgrid.append('0')
    grid.append(tmpgrid)

for y in range(height):
    for x in range(width):
        print(grid[x][y], end = '')
        if (y == height-1):

    print("y" + str(y))