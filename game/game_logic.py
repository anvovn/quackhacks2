import time
import math
import sys
import termios
import tty
from game import *

# Basic information 
NIGHT_DURATION = 10
NIGHT = 1
FLOOR_TIMER = 90

# Player won't have class (unless player complexity gets high enough to benefit from class usage)
PLAYER_HEALTH = 10
PLAYER_MOVEMENT = 1
PLAYER_ATTACK = 2

# Every enemy will inherit from this (including bosses because I'm lazy)
class BaseEnemy:
    def __init__(self, health=None, attack=None, movement=None):
        self.health = 0
        self.attack = 0
        self.movement = 0

    def attack(target):
        PLAYER_HEALTH = PLAYER_HEALTH - self.attack

    def receive_damage(damage):
        self.health = self.health - damage

    def isAlive():
        return self.health <= 0

# Basic enemies
class Ghost(BaseEnemy):
    def __init__(self, hp, attack, movement):
        super().__init__(5, 1, 1)

class Zombie(BaseEnemy):
    def __init__(self, hp, attack, movement):
        super().__init__(10, 2, 1)

#Night methods
def update_night(night):
    print(f'Night {NIGHT} has been completed!')
    NIGHT = night + 1
    time.sleep(5)
    if NIGHT != 6:
        print(f'Night {NIGHT} has begun')
        game_time_loop()
    elif NIGHT == 6:
        print(f'You survived Five Nights at the EMU!')
    
def restart_night(night):
    print(f'You died')
    time.sleep(5)
    game_time_loop()

def display_countdown(current_time):
    print(f'Time: {NIGHT_DURATION - current_time} s')

# Gameplay functions 
def floor_time_is_up():
    for i in range(10):
        Ghost()

def valid_attack(target):
    return

# The time loop so far
def game_time_loop():
    print(f'Night {NIGHT} has begun')
    start_time = time.time()
    while True:
        time_passed = time.time() - start_time
        remaining_time = math.floor(NIGHT_DURATION - time_passed)
        remaining_ft = math.floor(FLOOR_TIMER - time_passed)
        print(f'Time left: {remaining_time}')
        if remaining_time <= 0:
            update_night(NIGHT)
            break
        elif remaining_ft <= 0:
            floor_time_is_up()
        time.sleep(1)

# Movement
basic_solid = {"#", "E"}   # walls, enemies, etc—cannot walk through
pass_through = {"-", " ", "<", "?", "c", "p", "^", "v", "="}

def move_player(grid, value_grid, player_pos, direction):
    x, y = player_pos

    # movement offsets
    offsets = {
        "w": (0, -1),
        "s": (0, 1),
        "a": (-1, 0),
        "d": (1, 0)
    }

    if direction not in offsets:
        return player_pos  # no movement

    dx, dy = offsets[direction]
    nx, ny = x + dx, y + dy

    # bounds check
    if ny < 0 or ny >= len(grid): 
        return player_pos
    if nx < 0 or nx >= len(grid[0]):
        return player_pos

    tile_char = grid[ny][nx][0]
    tile_value = value_grid[ny][nx]

    # ------------------------------------------------
    # COLLISION / INTERACTION LOGIC
    # ------------------------------------------------

    # solid collision
    if tile_char in basic_solid:
        return player_pos

    # door collision (needs key)
    if tile_char == "=":
        print("Door blocked — you need a key!")
        return player_pos

    # Key pickup
    if tile_char == "<":
        print("Picked up a key!")
        # we could add key inventory logic later

    # Stairs
    if tile_char == "^":
        print("Stairs going UP")
    if tile_char == "v":
        print("Stairs going DOWN")

    # Chest
    if tile_char == "c":
        print("Opened chest!")

    # ------------------------------------------------
    # MOVE PLAYER (grid & value_grid)
    # ------------------------------------------------

    # Simply move the player position without modifying the grid.
    # The client will draw the player sprite on top of whatever tile is at this position.
    # Don't modify grid or value_grid — keep them intact so floor types are preserved.

    return (nx, ny)

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def main():
    game_time_loop()

if __name__ == "__main__":
    main()