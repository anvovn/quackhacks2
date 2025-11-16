// --- Connect to WebSocket server ---
const socket = new WebSocket("ws://localhost:8765");

// --- Canvas setup ---
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

// How big each tile should be on screen
const TILE_SIZE = 30;

let gameState = null;

// --- Receive game state from Python ---
socket.onmessage = (event) => {
    gameState = JSON.parse(event.data);
    drawGame();
};

// --- Send user input to Python ---
window.addEventListener("keydown", (ev) => {
    const key = ev.key.toLowerCase();

    if (["w", "a", "s", "d"].includes(key)) {
        socket.send(JSON.stringify({ move: key }));
    }
});

// --- Draw the game on canvas ---
function drawGame() {
    if (!gameState) return;

    const grid = gameState.grid;
    const player = gameState.player;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw grid
    for (let y = 0; y < grid.length; y++) {
        for (let x = 0; x < grid[y].length; x++) {
            const cell = grid[y][x];

            if (cell === 0) ctx.fillStyle = "#111";       // empty
            else if (cell === 1) ctx.fillStyle = "#888";  // wall
            else ctx.fillStyle = "#444";

            ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        }
    }

    // Draw player
    ctx.fillStyle = "yellow";
    ctx.fillRect(
        player.x * TILE_SIZE,
        player.y * TILE_SIZE,
        TILE_SIZE,
        TILE_SIZE
    );
}a