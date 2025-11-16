import os
import json
import asyncio
import websockets
from flask import Flask, render_template, send_from_directory
from threading import Thread

# Import your game modules
import sys
sys.path.insert(0, os.path.dirname(__file__))
from game import *
from game_logic import *
import game_state as GS  # <-- Use GS instead of globals

# --- Flask App Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)

@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/game')
@app.route('/game.html')
def game():
    return render_template('game.html')

@app.route('/end')
@app.route('/end.html')
def end():
    return render_template('end.html')

@app.route('/tutorial')
@app.route('/tutorial.html')
def tutorial():
    return render_template('tutorial.html')

@app.route('/credits')
@app.route('/credits.html')
def credits():
    return render_template('credits.html')

@app.route('/settings')
@app.route('/settings.html')
def settings():
    return render_template('settings.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_dir = os.path.join(BASE_DIR, 'assets')
    return send_from_directory(assets_dir, filename)

# --- Initialize Game State ---
level_path = os.path.join(BASE_DIR, 'assets/levels/level_0.txt')

def initialize_game():
    """Initialize or reset game state from the level file"""
    try:
        print(f"Loading level from: {level_path}")
        if not os.path.exists(level_path):
            raise FileNotFoundError(f"Level file not found: {level_path}")

        # Unpack returned values into GS
        GS.w, GS.h, GS.value_grid, GS.ct, GS.grid, GS.player_pos = make_grid(level_path)
        GS.floor = 0
        reset() # Resets collected keys and grid changes (doors)

        print(f"✓ Level loaded: {GS.w}x{GS.h}, player at {GS.player_pos}")
    except Exception as e:
        print(f"✗ Failed to load level: {e}")
        import traceback
        traceback.print_exc()

        # Fallback grid
        GS.w, GS.h = 10, 10
        GS.grid = [[' ' for _ in range(GS.w)] for _ in range(GS.h)]
        for i in range(GS.w):
            GS.grid[0][i] = GS.grid[GS.h-1][i] = '#'
            GS.grid[i][0] = GS.grid[i][GS.w-1] = '#'
        GS.player_pos = [5, 5]
        GS.value_grid = GS.grid  # simple fallback
        GS.basic_tiles = {}

# Initialize game on startup
initialize_game()

# --- Serialize GS for WebSocket ---
def serialize_state():
    msg = GS.message
    GS.message = None  # Clear message after sending
    return {
        "grid": GS.grid,
        "player": {"x": GS.player_pos[0], "y": GS.player_pos[1]},
        "basic_tiles": GS.basic_tiles,
        "message": msg,
        "game_complete": GS.game_complete
    }

# --- WebSocket Handler ---
async def handler(ws):
    # Reset game state for this new connection
    initialize_game()
    print(f"New client connected, game reset to initial state")
    
    while True:
        try:
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
                    GS.player_pos = move_player(direction)  # move_player returns new pos

            await asyncio.sleep(0.03)
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
            break

async def websocket_server():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("✓ WebSocket server running at ws://0.0.0.0:8765")
        await asyncio.Future()  # run forever

def run_websocket():
    asyncio.run(websocket_server())

# --- Main Execution ---
if __name__ == "__main__":
    # Start WebSocket server thread
    ws_thread = Thread(target=run_websocket, daemon=True)
    ws_thread.start()

    # Give WebSocket time to start
    import time
    time.sleep(1)

    # Start Flask server
    app.run(host="0.0.0.0", port=5000, debug=False)
