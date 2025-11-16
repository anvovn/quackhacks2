// Client renderer: connects to game server websocket and renders grid using server's basic_tiles
(function () {
  // Dynamic WebSocket URL - works for local, deployed, and Codespaces
  let WS_URL;
  
  // Check if we're in GitHub Codespaces (URL contains .github.dev or .app.github.dev)
  if (window.location.hostname.includes('github.dev') || window.location.hostname.includes('app.github.dev')) {
    // In Codespaces, use wss:// with the same hostname, different port
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    WS_URL = `${wsProtocol}//${window.location.hostname.replace('-5000.', '-8765.')}`;
    console.log('Detected Codespaces environment');
  } else {
    // Local or standard deployment
    WS_URL = `ws://${window.location.hostname}:8765`;
  }
  
  console.log('Connecting to WebSocket:', WS_URL);

  // Camera / viewport settings
  const VIEWPORT_WIDTH = window.innerWidth;   // canvas display size
  const VIEWPORT_HEIGHT = window.innerHeight;
  const TILE_SIZE = 64;         // fixed zoomed-in tile size (larger = more zoomed)
  const HALF_VIEWPORT_COLS = Math.floor(VIEWPORT_WIDTH / (TILE_SIZE * 2));
  const HALF_VIEWPORT_ROWS = Math.floor(VIEWPORT_HEIGHT / (TILE_SIZE * 2));

  const canvas = document.getElementById('gameCanvas');
  if (!canvas) {
    console.error('gameCanvas not found');
    return;
  }
  const ctx = canvas.getContext('2d');

  //Set up audio for footsteps
  let footstepAudio = new Audio('/assets/audio/footsteps.wav'); 

  //AUDIO END

  // set canvas to fixed viewport size
  canvas.style.width = VIEWPORT_WIDTH + 'px';
  canvas.style.height = VIEWPORT_HEIGHT + 'px';
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(VIEWPORT_WIDTH * dpr);
  canvas.height = Math.floor(VIEWPORT_HEIGHT * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  // Disable image smoothing for crisp pixel art
  ctx.imageSmoothingEnabled = false;
  ctx.webkitImageSmoothingEnabled = false;

    
  // Create an off-screen canvas for drawing the dim overlay
  const overlayCanvas = document.createElement('canvas');
  overlayCanvas.width = canvas.width;
  overlayCanvas.height = canvas.height;
  const overlayCtx = overlayCanvas.getContext('2d');
  overlayCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  overlayCtx.imageSmoothingEnabled = false;

  // Image cache to avoid reloading
  const imageCache = {};

  // Player direction tracking (0 = up, 90 = right, 180 = down, 270 = left)
  let playerDirection = 0; // starts facing up

  // Pause state
  let isPaused = false;
  let ws = null; // websocket will be assigned in connect()

  // Message display
  let messageTimeout = null;
  const MESSAGE_DURATION = 3000; // 3 seconds

  // last known server state
  let lastGrid = null;
  let lastPlayer = null;
  let serverTiles = null;

  // Display a message to the player
  function showMessage(text) {
    if (!text) return;
    const container = document.getElementById('messageContainer');
    container.textContent = text;
    container.classList.add('show');

    // Clear previous timeout if any
    if (messageTimeout) clearTimeout(messageTimeout);

    // Auto-hide after duration
    messageTimeout = setTimeout(() => {
      container.classList.remove('show');
    }, MESSAGE_DURATION);
  }

  // Load an image and cache it
  function loadImage(src) {
    if (imageCache[src]) return imageCache[src];
    const img = new Image();
    img.src = src;
    imageCache[src] = img;
    return img;
  }

  // Get sprite for a tile, handling numbered variants (e.g., "#1", "#2", " 1", " 2")
  function getSpriteForTile(tileStr) {
    const baseChar = tileStr[0];
    const suffix = tileStr.slice(1); // e.g., "1", "2"

    const spriteMap = {
      '-': '/assets/art/concrete_floor.png',        // empty
      '#': '/assets/art/concrete_wall.png',          // wall (default)
      ' ': '/assets/art/tile_floor.png',             // basic floor (default)
      '*': '/assets/art/duck_player.png',            // player
      '=': '/assets/art/door_template.png',          // door
      '<': '/assets/art/Keycard.png',                // keycard
      '?': '/assets/art/cardboard_box.png',          // interactable
      'E': '/assets/art/attack_roomba.png',          // enemy
      '^': '/assets/art/StairsVertical.png',         // staircase up
      'v': '/assets/art/StairsVertical.png',         // staircase down
      '@': '/assets/art/concrete_floor.png',         // start
      'c': '/assets/art/Chest.png',                  // chest
      'p': '/assets/art/cardboard_box.png'           // powerup
    };

    // Handle numbered wall variants
    if (baseChar === '#') {
      if (suffix === '0') return '/assets/art/concrete_wall.png';
      if (suffix === '1') return '/assets/art/wood_wall.png';
      return spriteMap['#'];
    }

    // Handle numbered floor variants
    if (baseChar === ' ') {
      if (suffix === '0') return '/assets/art/concrete_floor.png';
      if (suffix === '1') return '/assets/art/wood_floor.png';
      if (suffix === '2') return '/assets/art/green_carpet.png';
      if (suffix === '3') return '/assets/art/tile_floor.png';
      return spriteMap[' '];
    }

    return spriteMap[baseChar] || '/assets/art/concrete_floor.png';
  }

  function draw(state) {
    const grid = state.grid;
    const player = state.player;
    if (!Array.isArray(grid) || grid.length === 0) return;

    lastGrid = grid;
    lastPlayer = player;

    const gridRows = grid.length;
    const gridCols = grid[0].length;

    // Calculate camera position centered on player
    let cameraX = 0;
    let cameraY = 0;
    if (player && Number.isFinite(player.x) && Number.isFinite(player.y)) {
      cameraX = player.x - HALF_VIEWPORT_COLS;
      cameraY = player.y - HALF_VIEWPORT_ROWS;
      // Clamp to grid bounds
      cameraX = Math.max(0, Math.min(cameraX, gridCols - 2 * HALF_VIEWPORT_COLS - 1));
      cameraY = Math.max(0, Math.min(cameraY, gridRows - 2 * HALF_VIEWPORT_ROWS - 1));
    }

    // clear canvas
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT);

    // Calculate which tiles to render (only those visible in viewport)
    const startCol = Math.floor(cameraX);
    const startRow = Math.floor(cameraY);
    const endCol = Math.min(gridCols, startCol + Math.ceil(VIEWPORT_WIDTH / TILE_SIZE) + 1);
    const endRow = Math.min(gridRows, startRow + Math.ceil(VIEWPORT_HEIGHT / TILE_SIZE) + 1);

    // Draw tiles
    for (let y = startRow; y < endRow; y++) {
      for (let x = startCol; x < endCol; x++) {
        const cell = String(grid[y][x] || ' ');
        const key = cell[0];
        
        // Skip drawing the player tile; it will be drawn on top at the end
        if (key === '*') continue;

        // Calculate screen position
        const screenX = (x - cameraX) * TILE_SIZE;
        const screenY = (y - cameraY) * TILE_SIZE;

        // Get sprite path for this tile (handles numbered variants like #1, #2, etc.)
        const spritePath = getSpriteForTile(cell);
        const sprite = loadImage(spritePath);

        if (sprite && sprite.complete) {
          // draw sprite if loaded
          ctx.drawImage(sprite, screenX, screenY, TILE_SIZE, TILE_SIZE);
        } else {
          // fallback color if sprite not loaded yet
          ctx.fillStyle = '#555';
          ctx.fillRect(screenX, screenY, TILE_SIZE, TILE_SIZE);
        }
      }
    }

    // draw player sprite centered on screen
    if (player && Number.isFinite(player.x) && Number.isFinite(player.y)) {
      const screenX = (player.x - cameraX) * TILE_SIZE;
      const screenY = (player.y - cameraY) * TILE_SIZE;
      const playerSpritePath = getSpriteForTile('*');
      const pSprite = loadImage(playerSpritePath);
      
      // Save canvas state
      ctx.save();
      
      // Translate to center of sprite, rotate, then translate back
      const centerX = screenX + TILE_SIZE / 2;
      const centerY = screenY + TILE_SIZE / 2;
      ctx.translate(centerX, centerY);
      ctx.rotate(playerDirection * Math.PI / 180);
      ctx.translate(-TILE_SIZE / 2, -TILE_SIZE / 2);
      
      if (pSprite && pSprite.complete) {
        ctx.drawImage(pSprite, 0, 0, TILE_SIZE, TILE_SIZE);
      } else {
        // fallback circle
        ctx.beginPath();
        ctx.fillStyle = '#ffd700';
        ctx.arc(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE * 0.35, 0, Math.PI * 2);
        ctx.fill();
        ctx.closePath();
      }
      
      // Restore canvas state
      ctx.restore();
    }

    // Draw dim overlay and vision cone using off-screen canvas
    if (player && Number.isFinite(player.x) && Number.isFinite(player.y)) {
      const playerScreenX = (player.x - cameraX + 0.5) * TILE_SIZE;
      const playerScreenY = (player.y - cameraY + 0.5) * TILE_SIZE;
      const visionRadius = 250; // how far the light reaches
      const visionAngle = 360; // degrees (360° = full circle)
      const visionDirection = 0;

      // Convert to radians and calculate start/end angles
      const startAngle = (visionDirection - visionAngle / 2) * (Math.PI / 180);
      const endAngle = (visionDirection + visionAngle / 2) * (Math.PI / 180);

      // Clear overlay canvas
      overlayCtx.clearRect(0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT);

      // Draw on overlay canvas: fill with dim, then cut out the vision cone
      overlayCtx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      overlayCtx.fillRect(0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT);

      // Cut out the vision cone (use destination-out to erase)
      overlayCtx.globalCompositeOperation = 'destination-out';
      overlayCtx.fillStyle = 'rgba(0, 0, 0, 1)';
      overlayCtx.beginPath();
      overlayCtx.arc(playerScreenX, playerScreenY, visionRadius, startAngle, endAngle);
      overlayCtx.lineTo(playerScreenX, playerScreenY);
      overlayCtx.closePath();
      overlayCtx.fill();

      // Reset composite operation
      overlayCtx.globalCompositeOperation = 'source-over';

      // Draw the overlay canvas onto the main canvas
      ctx.drawImage(overlayCanvas, 0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
    } else {
      // If no player, just dim everything
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
    }
  }

  // reconnecting websocket with simple backoff
  function connect() {
    ws = new WebSocket(WS_URL);
    ws.addEventListener('open', () => console.log('WS open', WS_URL));
    ws.addEventListener('message', (evt) => {
      try {
        const state = JSON.parse(evt.data);
        // server may send `basic_tiles` mapping; store it
        if (state.basic_tiles) {
          serverTiles = state.basic_tiles;
          console.debug('Received basic_tiles from server', serverTiles);
        }
        // Show message if server sent one
        if (state.message) {
          showMessage(state.message);
        }
        draw(state);
      } catch (err) {
        console.error('Failed to parse state', err, evt.data);
      }
    });
    ws.addEventListener('close', () => {
      console.log('WS closed — reconnecting in 1s');
      setTimeout(connect, 1000);
    });
    ws.addEventListener('error', (e) => {
      console.error('WS error', e);
      ws.close();
    });

    // forward keyboard input and update player direction
    window.addEventListener('keyup', (ev) => {
      // Stop footstep audio when key is released
      footstepAudio.pause(); 
      footstepAudio.currentTime = 0;
    });
    
    window.addEventListener('keydown', (ev) => {
      // Don't send movement commands if paused
      if (isPaused) return;
      
      const keyMap = { 
        ArrowUp: 'w', ArrowLeft: 'a', ArrowDown: 's', ArrowRight: 'd', 
        w: 'w', a: 'a', s: 's', d: 'd' 
      };
      const mv = keyMap[ev.key];
      
      // Update player direction based on key pressed
      if (ev.key === 'w' || ev.key === 'ArrowUp') playerDirection = 0;      // up
      else if (ev.key === 'd' || ev.key === 'ArrowRight') playerDirection = 90;  // right
      else if (ev.key === 's' || ev.key === 'ArrowDown') playerDirection = 180;  // down
      else if (ev.key === 'a' || ev.key === 'ArrowLeft') playerDirection = 270;  // left
      
      if (mv) {
        // Play footstep audio
        footstepAudio.play();
        
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ move: mv }));
        }
      }
    });
  }

  // prevent page scrolling and set margins
  document.documentElement.style.overflow = 'hidden';
  document.body.style.margin = '0';
  document.body.style.overflow = 'hidden';

  // Set up pause menu functionality
  const pauseButton = document.getElementById('pauseButton');
  const pauseMenu = document.getElementById('pauseMenu');
  const resumeButton = document.getElementById('resumeButton');
  const menuButton = document.getElementById('menuButton');

  if (pauseButton) {
    pauseButton.addEventListener('click', () => {
      isPaused = true;
      pauseMenu.classList.remove('hidden');
    });
  }

  if (resumeButton) {
    resumeButton.addEventListener('click', () => {
      isPaused = false;
      pauseMenu.classList.add('hidden');
    });
  }

  if (menuButton) {
    menuButton.addEventListener('click', () => {
      // Close websocket and redirect to menu
      if (ws) ws.close();
      window.location.href = 'index.html';
    });
  }

  // Also allow ESC key to toggle pause
  window.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') {
      if (isPaused) {
        isPaused = false;
        if (pauseMenu) pauseMenu.classList.add('hidden');
      } else {
        isPaused = true;
        if (pauseMenu) pauseMenu.classList.remove('hidden');
      }
    }
  });

  connect();

})();