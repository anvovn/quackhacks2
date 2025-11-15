// --- Setup ---
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

// Example game state
let player = {
  x: 100,
  y: 100,
  size: 40,
  speed: 3
};

let keys = {}; // store pressed keys

// --- Input Handling ---
window.addEventListener("keydown", (e) => keys[e.key] = true);
window.addEventListener("keyup", (e) => keys[e.key] = false);

// --- Update Game Logic ---
function update() {
  if (keys["ArrowUp"])    player.y -= player.speed;
  if (keys["ArrowDown"])  player.y += player.speed;
  if (keys["ArrowLeft"])  player.x -= player.speed;
  if (keys["ArrowRight"]) player.x += player.speed;
}

// --- Draw Everything ---
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = "cyan";
  ctx.fillRect(player.x, player.y, player.size, player.size);
}

// --- Game Loop ---
function gameLoop() {
  update();
  draw();
  requestAnimationFrame(gameLoop);
}

gameLoop();