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

// rotation in radians; 0 = no rotation
player.rotation = 0;
player.rotationSpeed = 0.06; // radians per frame when arrow pressed

let keys = {}; // store pressed keys (normalized to lowercase)

// --- Input Handling ---
window.addEventListener("keydown", (e) => {
  // normalize to lowercase so we handle 'w' and 'W' the same
  keys[e.key.toLowerCase()] = true;
});
window.addEventListener("keyup", (e) => {
  keys[e.key.toLowerCase()] = false;
});

// --- Update Game Logic ---
function update() {
  // WASD controls (use lowercase keys because we normalize input)
  if (keys['w']) player.y -= player.speed;
  if (keys['s']) player.y += player.speed;
  if (keys['a']) player.x -= player.speed;
  if (keys['d']) player.x += player.speed;
  // Arrow keys rotate the player model (use normalized keys: 'arrowleft' / 'arrowright')
  if (keys['arrowleft']) {
    player.rotation -= player.rotationSpeed;
  }
  if (keys['arrowright']) {
    player.rotation += player.rotationSpeed;
  }

  // Keep rotation in a reasonable range (optional normalization)
  if (player.rotation > Math.PI * 2) player.rotation -= Math.PI * 2;
  if (player.rotation < -Math.PI * 2) player.rotation += Math.PI * 2;
}

// --- Draw Everything ---
function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw rotated player square centered on (player.x, player.y)
  const cx = player.x + player.size / 2;
  const cy = player.y + player.size / 2;

  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(player.rotation);
  ctx.fillStyle = "cyan";
  // draw centered at origin because we've translated to center
  ctx.fillRect(-player.size / 2, -player.size / 2, player.size, player.size);
  ctx.restore();
}

// --- Game Loop ---
function gameLoop() {
  update();
  draw();
  requestAnimationFrame(gameLoop);
}

gameLoop();