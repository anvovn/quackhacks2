from game_logic import *
from game import *
import os, time

import game_state as GS
from game_logic import *

def main():
    w, h, vg, ct, GS.grid, GS.player_pos = make_grid("floor0.txt")
    GS.vg = vg
    GS.ct = ct
    GS.w = w
    GS.h = h

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        for row in GS.grid:
            print("".join(row))

        key = getch().lower()
        if key == "q":
            break
        if key in ("w","a","s","d"):
            GS.player_pos = move_player(key)  # still updates position

if __name__ == "__main__":
    main()