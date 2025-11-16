# game_logic.py
import sys
import time
import math
import termios
import tty
import game_state as GS
from game import make_grid

# ============================================================
#  MODULE-LOCAL RUNTIME STATE
# ============================================================
NIGHT_DURATION = 10
NIGHT = 1
FLOOR_TIMER = 90

PLAYER_HEALTH = 10
PLAYER_ATTACK = 2

collectedKeys = set()     # set of key ids collected
gridChanges = []          # list of (floor, x, y, state0, state1)
enemyStates = []          # placeholder for enemy instances/state

# ============================================================
#  BASIC ENEMY CLASS (kept simple)
# ============================================================
class Roomba:
    def __init__(self, hp=3, attack=1, movement=1):
        self.hp = hp
        self.attack = attack
        self.movement = movement

    def do_attack(self):
        global PLAYER_HEALTH
        PLAYER_HEALTH -= self.attack

    def receive_damage(self, dmg):
        self.hp -= dmg

    def is_alive(self):
        return self.hp > 0

# ============================================================
#  HELPERS / CONFIG
# ============================================================
basic_solid = {"#", "E"}   # cannot walk through
pass_through = {"-", " ", "<", "?", "c", "p", "^", "v", "="}

def display_countdown(t):
    print(f"Time: {max(0, NIGHT_DURATION - t)} s")

def floor_time_is_up():
    print("Floor time is up!")

# ============================================================
#  ADJACENT FLOOR TILE RESOLUTION (uses GS.value_grid)
# ============================================================
from collections import Counter

def getAdjacentFloorTile(x, y):
    """
    Return the cell[1] value that is most common among the four cardinal neighbors.
    Only return it if the associated cell[0] is 2, otherwise return 0.
    """
    neighbors = [(1,0), (-1,0), (0,1), (0,-1)]
    values = []

    for dx, dy in neighbors:
        nx, ny = x + dx, y + dy
        if 0 <= ny < GS.h and 0 <= nx < GS.w:
            cell = GS.value_grid[ny][nx]
            if isinstance(cell, (list, tuple)) and len(cell) > 1:
                if int(cell[0]) == 2:
                    values.append(cell[1])
            elif isinstance(cell, dict):
                if int(cell.get("floor", 0)) == 2:
                    values.append(cell.get("subtile", 0))  # or whatever corresponds to cell[1]

    if not values:
        return 0

    most_common_value = Counter(values).most_common(1)[0][0]
    GS.grid[y][x] = " "
    return most_common_value


# ============================================================
#  GRID CHANGE PERSISTENCE
# ============================================================
def add_gridchange(floor, x, y, state0, state1):
    """
    Record a change and apply it immediately if it matches current floor.
    Also update GS.grid so clients see the visual change.
    """
    gridChanges.append((floor, x, y, state0, state1))

    if getattr(GS, "floor", None) == floor:
        try:
            # apply to value_grid if structure supports indexing
            if state0 is not None and isinstance(GS.value_grid[y][x], (list, tuple)):
                GS.value_grid[y][x][0] = state0
            else:
                # try to set completely if not list-like
                GS.value_grid[y][x] = [state0, state1]

            if state1 is not None:
                if isinstance(GS.value_grid[y][x], list):
                    GS.value_grid[y][x][1] = state1

            # update visual char in GS.grid using chestTable (GS.ct) or fallback:
            try:
                GS.grid[y][x] = GS.ct[state0]
            except Exception:
                # fallback: if GS.ct missing or state0 invalid, use floor char ' '
                GS.grid[y][x] = " "
        except Exception:
            # fail silently to avoid crashing runtime; log optionally
            print("[add_gridchange] failed to apply immediate change at", (x, y))

# ============================================================
#  LEVEL LOADING
# ============================================================
def load_level(new_floor, start_pos=None):
    """
    Load a level into GS.* and apply saved gridChanges for that floor.
    new_floor may be int or string convertible to int.
    """
    try:
        nf = int(new_floor)
    except Exception:
        print("[load_level] invalid floor:", new_floor)
        return False

    fname = f"level_{nf}.txt"
    try:
        w, h, vg, ct, grid, player_pos = make_grid(fname)
    except Exception as e:
        print(f"[load_level] make_grid failed for {fname}: {e}")
        return False

    GS.w = w
    GS.h = h
    GS.value_grid = vg
    GS.ct = ct
    GS.grid = grid
    if start_pos:
        try:
            GS.player_pos = tuple(start_pos)
        except Exception:
            GS.player_pos = player_pos
    else:
        GS.player_pos = player_pos
    GS.floor = nf

    # apply recorded changes for this floor
    for rec in gridChanges:
        if rec[0] != nf:
            continue
        _, gx, gy, s0, s1 = rec
        try:
            if 0 <= gy < GS.h and 0 <= gx < GS.w:
                # ensure underlying structure is list-like
                if isinstance(GS.value_grid[gy][gx], (list, tuple)):
                    GS.value_grid[gy][gx][0] = s0
                    GS.value_grid[gy][gx][1] = s1
                else:
                    GS.value_grid[gy][gx] = [s0, s1]
                try:
                    GS.grid[gy][gx] = GS.ct[s0]
                except Exception:
                    GS.grid[gy][gx] = " "
        except Exception:
            pass

    return True

def new_level(new_floor, start_pos=None):
    return load_level(new_floor, start_pos)

# ============================================================
#  MOVEMENT (uses GS globals) - call as move_player(direction)
# ============================================================
def move_player(direction):
    # print("PMV")
    """
    Use GS.grid, GS.value_grid, GS.player_pos, GS.h, GS.w.
    Returns GS.player_pos (possibly updated).
    """
    global collectedKeys

    if not hasattr(GS, "grid") or not hasattr(GS, "value_grid"):
        print("[move_player] GS.grid or GS.value_grid not initialized")
        return getattr(GS, "player_pos", (0,0))

    x, y = GS.player_pos
    grid = GS.grid
    vg = GS.value_grid

    offsets = {"w": (0,-1), "s": (0,1), "a": (-1,0), "d": (1,0)}
    if direction not in offsets:
        return GS.player_pos

    dx, dy = offsets[direction]
    nx, ny = x + dx, y + dy

    # bounds
    if ny < 0 or ny >= GS.h:
        return GS.player_pos
    if nx < 0 or nx >= GS.w:
        return GS.player_pos

    # tile char and value
    tile_cell = grid[ny][nx]
    tile_char = tile_cell[0] if isinstance(tile_cell, str) and tile_cell else tile_cell
    try:
        tile_val = vg[ny][nx]
    except Exception:
        tile_val = None

    # solid collision: walls and enemies
    if tile_char in basic_solid:
        return GS.player_pos

    # DOOR: block unless key present
    # DOOR: block unless key present
    if tile_char == "=":
        key_id = tile_val[1] if isinstance(tile_val, (list, tuple)) and len(tile_val) > 1 else None
        if key_id in collectedKeys:
            new_floor = getAdjacentFloorTile(nx, ny)
            # convert door to floor and clear key ID
            add_gridchange(GS.floor, nx, ny, 2, new_floor)
            print("Door unlocked.")
            GS.message = "Door unlocked."
            # now move player onto the tile
            GS.player_pos = (nx, ny)
            return GS.player_pos
        else:
            print("Door blocked — need key:", key_id)
            GS.message = f"Door blocked — need key: {key_id}"
            return GS.player_pos


    # KEY pickup: walk onto it and pick it up
    if tile_char == "<":
        key_id = tile_val[1] if isinstance(tile_val, (list, tuple)) and len(tile_val) > 1 else None
        collectedKeys.add(key_id)
        print(f"Picked up a key: {key_id}")
        GS.message = f"Picked up a key: {key_id}"
        new_floor = getAdjacentFloorTile(nx, ny)
        # convert tile to floor and clear key ID
        add_gridchange(GS.floor, nx, ny, 2, new_floor)
        GS.player_pos = (nx, ny)
        return GS.player_pos


    # Stairs up/down
    if tile_char == "=":
        key_id = tile_val[1] if isinstance(tile_val, (list, tuple)) and len(tile_val) > 1 else None
        if key_id in collectedKeys:
            new_floor = getAdjacentFloorTile(nx, ny)
            # convert door to floor and clear key ID
            add_gridchange(GS.floor, nx, ny, 2 , new_floor)
            print("Door unlocked.")
        else:
            print("Door blocked — need key:", key_id)
            return GS.player_pos


    # Chest interaction
    if tile_char == "c":
        print("Opened chest!")
        # optional: change vg/grid, spawn loot etc.

    # default — move player to the new tile
    GS.player_pos = (nx, ny)
    return GS.player_pos

# ============================================================
#  Terminal getch helper
# ============================================================
def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch

# ============================================================
#  Module test harness
# ============================================================
def main():
    print("game_logic loaded.")

if __name__ == "__main__":
    main()
