// Client renderer: connects to game server websocket and renders grid using server's basic_tiles
(function () {
  const WS_URL = "ws://localhost:8765";
  const ASSET_BASE = '/static/..';  // relative path to assets from static/

  const canvas = document.getElementById('gameCanvas');
  if (!canvas) {
    console.error('gameCanvas not found');
    return;
  }
  const ctx = canvas.getContext('2d');

  // Image cache to avoid reloading
  const imageCache = {};

  // last known server state
  let lastGrid = null;
  let lastPlayer = null;
  let serverTiles = null;

  // Load an image and cache it
  function loadImage(src) {
    if (imageCache[src]) return imageCache[src];
    const img = new Image();
    img.src = src;
    imageCache[src] = img;
    return img;
  }

  // Build a rendering map from server's basic_tiles object
  // Maps tile keys to sprite paths and fallback colors
  function buildTileMap(basicTiles) {
    const map = {};
    if (!basicTiles) return map;

    // Tile key -> sprite path mapping based on basic_tiles
    const spriteMap = {
      '-': '../assets/art/concrete_floor.png',        // empty → concrete floor
      '#': '../assets/art/concrete_wall.png',          // wall
      ' ': '../assets/art/tile_floor.png',             // basic floor (tile_floor)
      '*': '../assets/art/duck_player.png',            // player
      '=': '../assets/art/door_template.png',          // door
      '<': '../assets/art/Keycard.png',                // keycard
      '?': '../assets/art/cardboard_box.png',          // interactable
      'E': '../assets/art/attack_roomba.png',          // enemy
      '^': '../assets/art/StairsVertical.png',         // staircase up
      'v': '../assets/art/StairsVertical.png',         // staircase down (can reuse up)
      '@': '../assets/art/concrete_floor.png',         // start (concrete floor)
      'c': '../assets/art/Chest.png',                  // chest
      'p': '../assets/art/cardboard_box.png'           // powerup (can reuse box)
    };

    // For each tile key from basic_tiles, create a sprite entry
    Object.keys(basicTiles).forEach((k) => {
      const spritePath = spriteMap[k];
      map[k] = {
        name: String(k),
        sprite: spritePath ? loadImage(spritePath) : null,
        fallbackColor: '#999'
      };
    });

    return map;
  }

  // Fit canvas to viewport given cols/rows and return tile size
  function computeTileSize(cols, rows) {
    const availW = window.innerWidth;
    const availH = window.innerHeight;
    const tileByW = Math.floor(availW / Math.max(cols, 1));
    const tileByH = Math.floor(availH / Math.max(rows, 1));
    return Math.max(6, Math.floor(Math.min(tileByW, tileByH)));
  }

  function resizeCanvas(cols, rows, tileSize) {
    const dpr = window.devicePixelRatio || 1;
    const cssW = cols * tileSize;
    const cssH = rows * tileSize;
    canvas.style.width = cssW + 'px';
    canvas.style.height = cssH + 'px';
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    // prevent page scrolling and margins so canvas fits cleanly
    document.documentElement.style.overflow = 'hidden';
    document.body.style.margin = '0';
    document.body.style.overflow = 'hidden';
  }

  function draw(state) {
    const grid = state.grid;
    const player = state.player;
    if (!Array.isArray(grid) || grid.length === 0) return;

    lastGrid = grid;
    lastPlayer = player;

    // build tile map from serverTiles if available
    const tileMap = serverTiles ? buildTileMap(serverTiles) : {};

    const rows = grid.length;
    const cols = grid[0].length;
    const tileSize = computeTileSize(cols, rows);
    resizeCanvas(cols, rows, tileSize);

    // clear (use CSS coordinates; ctx is scaled)
    ctx.clearRect(0, 0, cols * tileSize, rows * tileSize);

    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        const cell = String(grid[y][x] || ' ');
        const key = cell[0];
        
        // Skip drawing the player tile here; it will be drawn on top at the end
        if (key === '*') continue;
        
        const tile = tileMap[key];

        if (tile && tile.sprite && tile.sprite.complete) {
          // draw sprite if loaded
          ctx.drawImage(tile.sprite, x * tileSize, y * tileSize, tileSize, tileSize);
        } else if (tile && tile.fallbackColor) {
          // fallback color if sprite not loaded yet
          ctx.fillStyle = tile.fallbackColor;
          ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
        } else {
          // unknown tile
          ctx.fillStyle = '#999';
          ctx.fillRect(x * tileSize, y * tileSize, tileSize, tileSize);
        }

        // draw small tile number if present
        if (cell.length > 1) {
          ctx.fillStyle = 'rgba(0,0,0,0.8)';
          const fontSize = Math.max(8, Math.floor(tileSize * 0.28));
          ctx.font = `bold ${fontSize}px Arial`;
          ctx.fillText(cell.slice(1), x * tileSize + 3, y * tileSize + Math.floor(fontSize + 1));
        }
      }
    }

    // draw player (as a sprite if available, else as a circle)
    if (player && Number.isFinite(player.x) && Number.isFinite(player.y)) {
      const px = player.x * tileSize;
      const py = player.y * tileSize;
      const pTile = tileMap['*'];
      if (pTile && pTile.sprite && pTile.sprite.complete) {
        ctx.drawImage(pTile.sprite, px, py, tileSize, tileSize);
      } else {
        // fallback circle
        ctx.beginPath();
        ctx.fillStyle = '#ffd700';
        ctx.arc(px + tileSize / 2, py + tileSize / 2, tileSize * 0.35, 0, Math.PI * 2);
        ctx.fill();
        ctx.closePath();
      }
    }
  }

  // reconnecting websocket with simple backoff
  function connect() {
    const ws = new WebSocket(WS_URL);
    ws.addEventListener('open', () => console.log('WS open', WS_URL));
    ws.addEventListener('message', (evt) => {
      try {
        const state = JSON.parse(evt.data);
        // server may send `basic_tiles` mapping; store it
        if (state.basic_tiles) {
          serverTiles = state.basic_tiles;
          console.debug('Received basic_tiles from server', serverTiles);
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

    // forward keyboard input
    window.addEventListener('keydown', (ev) => {
      const keyMap = { ArrowUp: 'w', ArrowLeft: 'a', ArrowDown: 's', ArrowRight: 'd', w: 'w', a: 'a', s: 's', d: 'd' };
      const mv = keyMap[ev.key];
      if (mv && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ move: mv }));
    });
  }

  // redraw on window resize using last known state
  window.addEventListener('resize', () => {
    if (lastGrid) draw({ grid: lastGrid, player: lastPlayer });
  });

  connect();

})();

