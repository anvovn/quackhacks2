from game_logic import *
from game import *
import os, time

def print_grid(grid):
    for row in grid:
        print("".join(row))

def main():
    w, h, vg, ct, grid, player_pos = make_grid("floor0.txt")

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print_grid(grid)
        key = getch().lower()
        if key == "q":
            break
        if key in ("w", "a", "s", "d"):
            player_pos = move_player(grid, vg, player_pos, key)

        time.sleep(0.1)

if __name__ == "__main__":
    main()