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

# --- Flask App Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, 
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'))

@app.route('/')
def main_page():
    return render_template('index.html')

@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/game')
@app.route('/game.html')
def game():
    return render_template('game.html')

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

# --- WebSocket Game Server ---
level_path = os.path.join(BASE_DIR, 'assets/levels/floor0new.txt')

# Initialize game state with error handling
try:
    print(f"Loading level from: {level_path}")
    if not os.path.exists(level_path):
        print(f"ERROR: Level file not found at {level_path}")
        print(f"Contents of assets dir: {os.listdir(os.path.join(BASE_DIR, 'assets'))}")
        raise FileNotFoundError(f"Level file not found: {level_path}")
    
    w, h, vg, ct, grid, player_pos = make_grid(level_path)
    print(f"✓ Level loaded successfully: {w}x{h} grid, player at {player_pos}")
except Exception as e:
    print(f"✗ Failed to load level: {e}")
    import traceback
    traceback.print_exc()
    # Create a minimal fallback grid
    print("Creating fallback 10x10 grid...")
    grid = [[' ' for _ in range(10)] for _ in range(10)]
    for i in range(10):
        grid[0][i] = grid[9][i] = grid[i][0] = grid[i][9] = '#'
    player_pos = [5, 5]
    vg = grid  # Simplified visibility grid
    w, h = 10, 10

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
                    player_pos = move_player(grid, vg, player_pos, direction)
            
            await asyncio.sleep(0.03)
        except websockets.exceptions.ConnectionClosed:
            break

async def websocket_server():
    try:
        # Bind to 0.0.0.0 to accept connections from outside the container
        async with websockets.serve(handler, "0.0.0.0", 8765):
            print("✓ WebSocket server running at ws://0.0.0.0:8765")
            print("  Clients can connect via ws://<your-ip>:8765")
            await asyncio.Future()
    except Exception as e:
        print(f"✗ WebSocket server failed to start: {e}")
        import traceback
        traceback.print_exc()

def run_websocket():
    try:
        print("WebSocket thread started, initializing asyncio...")
        asyncio.run(websocket_server())
    except Exception as e:
        print(f"✗ WebSocket thread crashed: {e}")
        import traceback
        traceback.print_exc()

# --- Main Execution ---
if __name__ == "__main__":
    # Debug: Print paths to verify
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"Templates: {os.path.join(BASE_DIR, 'templates')}")
    print(f"Static: {os.path.join(BASE_DIR, 'static')}")
    print(f"Assets: {os.path.join(BASE_DIR, 'assets')}")
    
    # Start WebSocket server in separate thread
    print("Starting WebSocket server thread...")
    ws_thread = Thread(target=run_websocket, daemon=True)
    ws_thread.start()
    
    # Give WebSocket time to start
    import time
    time.sleep(1)
    
    # Start Flask server
    print("Flask server starting on http://0.0.0.0:5000")
    print("Game page will be at http://0.0.0.0:5000/game")
    app.run(host="0.0.0.0", port=5000, debug=False)