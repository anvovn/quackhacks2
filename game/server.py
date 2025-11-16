import os
import re
import json
from game import *
from game_logic import *
import time
import asyncio
import websockets

# --- Initialize game ---
w, h, vg, ct, grid, player_pos = make_grid("floor0new.txt")

def serialize_state():
    try:
        tiles = basic_tiles
    except NameError:
        tiles = {}

    return {
        "grid": grid,
        "player": {"x": player_pos[0], "y": player_pos[1]},
        "basic_tiles": tiles
    }

async def handler(ws):
    global player_pos, vg, grid
    while True:
        # Send game state
        await ws.send(json.dumps(serialize_state()))

        # Receive input from JS
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=0.03)
        except asyncio.TimeoutError:
            msg = None

        if msg:
            data = json.loads(msg)
            direction = data.get("move")
            if direction in ("w", "a", "s", "d"):
                player_pos = move_player(grid, vg, player_pos, direction)

        await asyncio.sleep(0.03)

async def main():
    async with websockets.serve(handler, "localhost", 8765):
        print("Server running at ws://localhost:8765")
        await asyncio.Future()

asyncio.run(main())
