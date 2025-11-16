#!/usr/bin/env python3
"""
Full tile editor with:
- resizable window
- bottom UI panel with wrapping
- pan/zoom, auto-expand map (adds empty rows/cols BEFORE on negative pan)
- save/load (Shift+S / Shift+L) with trimmed width/height header
- eyedropper (E), drag-paint, forced numbers for -1 tiles, numbers shown on tiles
- art loading with error texture fallback
"""

import os
import pygame
import sys

# -------------------- CONFIG --------------------
TILE_SIZE = 32
# initial viewport tile counts (recalculated on window resize)
VIEW_WIDTH = 16
VIEW_HEIGHT = 16

# initial map size (can expand)
MAP_WIDTH = 100
MAP_HEIGHT = 100

# assets dir (change if needed)
ASSETS_DIR = os.path.join("..", "assets", "art")

basic_tiles = {
    "-": [0, -2],  # empty
    "#": [1, -1],  # wall
    " ": [2, -1],  # floor
    "*": [3, -2],  # player
    "=": [9, -1],  # door
    "<": [8, -1],  # keycard
    "?": [7, -1],  # interactable
    "E": [0, -1],  # enemy
    "^": [11, -1], # stair up
    "v": [12, -1], # stair down
    "@": [13, -1], # from stair
    "c": [21, -1], # chest
    "p": [22, -1]  # powerup
}

TILE_COLORS = {
    "-": (30, 30, 30),
    "#": (100,100,100),
    " ": (200,200,200),
    "*": (255,0,0),
    "=": (255,255,0),
    "<": (0,255,255),
    "?": (255,0,255),
    "E": (0,0,0),
    "^": (0,255,0),
    "v": (0,200,0),
    "@": (0,100,0),
    "c": (139,69,19),
    "p": (255,165,0)
}

UI_PANEL_HEIGHT = 110  # height for bottom UI panel (wraps text here)

# -------------------- PYGAME INIT --------------------
pygame.init()
# window starts resizable
SCREEN_WIDTH = max(900, VIEW_WIDTH * TILE_SIZE)
SCREEN_HEIGHT = max(700, VIEW_HEIGHT * TILE_SIZE + UI_PANEL_HEIGHT)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Tile Editor")
base_font = pygame.font.SysFont(None, 18)

# -------------------- GLOBAL STATE --------------------
tile_map = [["-" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
offset_x = 0
offset_y = 0

tile_keys = list(basic_tiles.keys())
selected_index = 1
selected_tile = tile_keys[selected_index]
pending_value = ""  # typed integer for -1 tiles

dragging = False
paint_tile = selected_tile

IMAGE_CACHE = {}  # (char,num,size) -> Surface
clock = pygame.time.Clock()

# -------------------- ERROR TEXTURE --------------------
# Try to load error.png, otherwise create a magenta X surface
def make_error_texture(size):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill((255, 0, 255))
    pygame.draw.line(surf, (0,0,0), (0,0), (size,size), max(2, size//8))
    pygame.draw.line(surf, (0,0,0), (size,0), (0,size), max(2, size//8))
    return surf

if os.path.exists(os.path.join(ASSETS_DIR, "error.png")):
    try:
        ERROR_TEXTURE_BASE = pygame.image.load(os.path.join(ASSETS_DIR, "error.png")).convert_alpha()
    except Exception:
        ERROR_TEXTURE_BASE = make_error_texture(64)
else:
    ERROR_TEXTURE_BASE = make_error_texture(64)

# -------------------- IMAGE LOADER WITH ERROR FALLBACK --------------------
def load_tile_image(char, num, size):
    """
    Safe loader that maps char+num -> filepath(s), loads & scales,
    returns ERROR_TEXTURE if anything goes wrong.
    """
    key = (char, num, size)
    if key in IMAGE_CACHE:
        return IMAGE_CACHE[key]

    try:
        # map char/num to file path (edit as needed to match your files)
        # floors/walls use different images depending on num variant
        path = None

        if char == "#":
            path = os.path.join(ASSETS_DIR, "wood_wall.png") if num == "1" else os.path.join(ASSETS_DIR, "concrete_wall.png")
        elif char == " ":
            if num == "1":
                path = os.path.join(ASSETS_DIR, "wood_floor.png")
            elif num == "2":
                path = os.path.join(ASSETS_DIR, "green_carpet.png")
            elif num == "3":
                path = os.path.join(ASSETS_DIR, "tile_floor.png")
            else:
                path = os.path.join(ASSETS_DIR, "concrete_floor.png")
        elif char == "*":
            path = os.path.join(ASSETS_DIR, "duck_player.png")
        elif char == "=":
            path = os.path.join(ASSETS_DIR, "door_templates.png")
        elif char == "<":
            path = os.path.join(ASSETS_DIR, "cardboard_box.png")
        elif char == "c":
            path = os.path.join(ASSETS_DIR, "Chest.png")
        elif char == "p":
            path = os.path.join(ASSETS_DIR, "cardboard_box.png")
        elif char == "E":
            # try specific roomba variants first
            if num and num.isdigit():
                candidate = os.path.join(ASSETS_DIR, f"roomba_{num}.png")
                if os.path.exists(candidate):
                    path = candidate
            if path is None:
                candidate = os.path.join(ASSETS_DIR, "roomba.png")
                if os.path.exists(candidate):
                    path = candidate
                else:
                    path = None
        elif char in ("^","v","@"):
            path = os.path.join(ASSETS_DIR, "tile_floor.png")
        elif char == "?":
            path = os.path.join(ASSETS_DIR, "door_templates.png")
        else:
            path = None

        if path and os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            if img.get_width() != size or img.get_height() != size:
                img = pygame.transform.smoothscale(img, (size, size))
            IMAGE_CACHE[key] = img
            return img
        else:
            # no file found / not intended to have art
            tex = pygame.transform.smoothscale(ERROR_TEXTURE_BASE, (size, size))
            IMAGE_CACHE[key] = tex
            return tex

    except Exception as e:
        # print small debug message and return error texture scaled to size
        print(f"[ART ERROR] Could not load tile art for {char}{num}: {e}")
        tex = pygame.transform.smoothscale(ERROR_TEXTURE_BASE, (size, size))
        IMAGE_CACHE[key] = tex
        return tex

def clear_image_cache():
    IMAGE_CACHE.clear()

# -------------------- MAP EXPANSION --------------------
def expand_map_to_include(gx, gy):
    """
    Expand tile_map so (gx,gy) is inside. Adds empty columns/rows BEFORE existing content
    when gx<0 or gy<0 (your choice A). Adjusts offsets so camera continues to point at same cells.
    """
    global tile_map, MAP_WIDTH, MAP_HEIGHT, offset_x, offset_y

    add_left = add_top = add_right = add_bottom = 0

    if gx < 0:
        add_left = -gx
    if gy < 0:
        add_top = -gy
    if gx >= MAP_WIDTH:
        add_right = gx - (MAP_WIDTH - 1)
    if gy >= MAP_HEIGHT:
        add_bottom = gy - (MAP_HEIGHT - 1)

    if add_left or add_top or add_right or add_bottom:
        new_w = MAP_WIDTH + add_left + add_right
        new_h = MAP_HEIGHT + add_top + add_bottom
        new_map = [["-" for _ in range(new_w)] for _ in range(new_h)]
        # copy old into new at offset (add_top, add_left)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                new_map[y + add_top][x + add_left] = tile_map[y][x]
        tile_map = new_map
        MAP_WIDTH = new_w
        MAP_HEIGHT = new_h
        offset_x += add_left
        offset_y += add_top

def ensure_view_within_map():
    global offset_x, offset_y
    if offset_x < 0 or offset_y < 0:
        expand_map_to_include(offset_x, offset_y)
    if offset_x + VIEW_WIDTH > MAP_WIDTH or offset_y + VIEW_HEIGHT > MAP_HEIGHT:
        expand_map_to_include(offset_x + VIEW_WIDTH - 1, offset_y + VIEW_HEIGHT - 1)

# -------------------- TILE FORMAT --------------------
def get_tile_char_num(tile):
    if ":" in tile:
        ch, num = tile.split(":", 1)
        return ch, num
    if basic_tiles.get(tile, [0,-2])[1] == -1:
        return tile, "0"
    return tile, None

# -------------------- SAVE / LOAD --------------------
def compute_used_bbox():
    min_x, max_x = MAP_WIDTH, -1
    min_y, max_y = MAP_HEIGHT, -1
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if tile_map[y][x] != "-":
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
    if max_x == -1:
        return None
    return (min_x, min_y, max_x, max_y)

def save_map_text(filename="tilemap.txt"):
    bbox = compute_used_bbox()
    if not bbox:
        print("Map empty, nothing to save.")
        return
    min_x, min_y, max_x, max_y = bbox
    trimmed_w = max_x - min_x + 1
    trimmed_h = max_y - min_y + 1
    with open(filename, "w") as f:
        f.write(f"width = {trimmed_w}\n")
        f.write(f"height = {trimmed_h}\n")
        for y in range(min_y, max_y + 1):
            line = ""
            for x in range(min_x, max_x + 1):
                tile = tile_map[y][x]
                if ":" in tile:
                    ch, num = tile.split(":", 1)
                    line += f"{ch}{num}"
                else:
                    ch = tile
                    if basic_tiles.get(ch, [0,-2])[1] == -1:
                        line += f"{ch}0"
                    else:
                        line += ch
            f.write(line + "\n")
    print(f"Map saved to {filename} (trimmed {trimmed_w}x{trimmed_h})")

def parse_map_line_to_row(line):
    row = []
    i = 0
    while i < len(line):
        ch = line[i]
        i += 1
        num = ""
        while i < len(line) and line[i].isdigit():
            num += line[i]
            i += 1
        if num:
            row.append(f"{ch}:{num}")
        else:
            row.append(ch)
    return row

def load_map_text(filename="tilemap.txt"):
    global tile_map, MAP_WIDTH, MAP_HEIGHT, offset_x, offset_y
    if not os.path.exists(filename):
        print("File not found:", filename)
        return
    with open(filename, "r") as f:
        lines = [ln.rstrip("\n") for ln in f.readlines()]

    idx = 0
    file_w = file_h = None
    while idx < len(lines):
        ln = lines[idx].strip()
        if ln.startswith("width"):
            try:
                file_w = int(ln.split("=")[1].strip()); idx += 1; continue
            except Exception:
                file_w = None
        if ln.startswith("height"):
            try:
                file_h = int(ln.split("=")[1].strip()); idx += 1; continue
            except Exception:
                file_h = None
        break

    map_lines = lines[idx:]
    rows = [parse_map_line_to_row(ln) for ln in map_lines]
    new_h = len(rows)
    new_w = max((len(r) for r in rows), default=0)
    if file_w:
        new_w = max(new_w, file_w)
    if file_h:
        new_h = max(new_h, file_h)

    # Expand map to fit loaded file
    if new_w > MAP_WIDTH or new_h > MAP_HEIGHT:
        for row in tile_map:
            row.extend(["-"] * (new_w - MAP_WIDTH))
        for _ in range(new_h - MAP_HEIGHT):
            tile_map.append(["-"] * new_w)
        MAP_WIDTH = max(MAP_WIDTH, new_w)
        MAP_HEIGHT = max(MAP_HEIGHT, new_h)

    # ensure rows have required width
    for y in range(MAP_HEIGHT):
        if len(tile_map[y]) < new_w:
            tile_map[y].extend(["-"] * (new_w - len(tile_map[y])))

    # copy into top-left
    for y, r in enumerate(rows):
        for x, t in enumerate(r):
            tile_map[y][x] = t

    offset_x = 0
    offset_y = 0
    clear_image_cache()
    print(f"Loaded {filename} (size {new_w}x{new_h}) into editor")

# -------------------- PLACEMENT --------------------
def place_tile_at(gx, gy):
    expand_map_to_include(gx, gy)
    if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
        if basic_tiles[selected_tile][1] == -1:
            val = pending_value if pending_value else "0"
            tile_map[gy][gx] = f"{selected_tile}:{val}"
        else:
            tile_map[gy][gx] = selected_tile

# -------------------- UI TEXT WRAP --------------------
def wrap_text_lines(text, font, max_width):
    if not text:
        return [""]
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        candidate = (cur + " " + w).strip() if cur else w
        if font.size(candidate)[0] <= max_width:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            if font.size(w)[0] > max_width:
                # split long word by characters
                chunk = ""
                for ch in w:
                    if font.size(chunk + ch)[0] <= max_width:
                        chunk += ch
                    else:
                        lines.append(chunk)
                        chunk = ch
                cur = chunk
            else:
                cur = w
    if cur:
        lines.append(cur)
    return lines

# -------------------- VIEWPORT RECALC --------------------
def recalc_view_counts_from_window():
    global VIEW_WIDTH, VIEW_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT
    avail_w = max(64, SCREEN_WIDTH)
    avail_h = max(64, SCREEN_HEIGHT - UI_PANEL_HEIGHT)
    VIEW_WIDTH = max(4, avail_w // TILE_SIZE)
    VIEW_HEIGHT = max(3, avail_h // TILE_SIZE)

# -------------------- MAIN LOOP --------------------
def main_loop():
    global SCREEN_WIDTH, SCREEN_HEIGHT, screen
    global TILE_SIZE, VIEW_WIDTH, VIEW_HEIGHT, offset_x, offset_y
    global dragging, paint_tile, selected_index, selected_tile, pending_value

    recalc_view_counts_from_window()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                recalc_view_counts_from_window()
                clear_image_cache()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if my >= SCREEN_HEIGHT - UI_PANEL_HEIGHT:
                    # clicking UI area - ignore for painting
                    continue
                gx = mx // TILE_SIZE + offset_x
                gy = my // TILE_SIZE + offset_y
                if event.button == 1:
                    place_tile_at(gx, gy)
                    dragging = True
                    paint_tile = tile_map[gy][gx]
                elif event.button == 3:
                    expand_map_to_include(gx, gy)
                    tile_map[gy][gx] = "-"
                    dragging = True
                    paint_tile = "-"

            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging:
                mx, my = event.pos
                if my >= SCREEN_HEIGHT - UI_PANEL_HEIGHT:
                    continue
                gx = mx // TILE_SIZE + offset_x
                gy = my // TILE_SIZE + offset_y
                place_tile_at(gx, gy)

            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()

                # Save: Shift+S
                if event.key == pygame.K_s and (mods & pygame.KMOD_SHIFT):
                    save_map_text()
                    continue

                # Load: Shift+L
                if event.key == pygame.K_l and (mods & pygame.KMOD_SHIFT):
                    load_map_text("tilemap.txt")
                    continue

                # Eyedropper: E
                if event.key == pygame.K_e:
                    mx, my = pygame.mouse.get_pos()
                    if my >= SCREEN_HEIGHT - UI_PANEL_HEIGHT:
                        continue
                    gx = mx // TILE_SIZE + offset_x
                    gy = my // TILE_SIZE + offset_y
                    expand_map_to_include(gx, gy)
                    if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
                        tile = tile_map[gy][gx]
                        ch, num = get_tile_char_num(tile)
                        selected_tile = ch
                        pending_value = num if num else ""
                        if ch in tile_keys:
                            selected_index = tile_keys.index(ch)
                    continue

                # Switch tile
                if event.key == pygame.K_RIGHT:
                    selected_index = (selected_index + 1) % len(tile_keys)
                    selected_tile = tile_keys[selected_index]
                    pending_value = ""
                    continue
                if event.key == pygame.K_LEFT:
                    selected_index = (selected_index - 1) % len(tile_keys)
                    selected_tile = tile_keys[selected_index]
                    pending_value = ""
                    continue

                # Pan: WASD / Arrows (can go negative to expand top/left)
                if event.key in (pygame.K_w, pygame.K_UP):
                    offset_y -= 1
                    ensure_view_within_map()
                    continue
                if event.key in (pygame.K_s, pygame.K_DOWN):
                    offset_y += 1
                    ensure_view_within_map()
                    continue
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    offset_x -= 1
                    ensure_view_within_map()
                    continue
                if event.key in (pygame.K_d, pygame.K_RIGHT):
                    offset_x += 1
                    ensure_view_within_map()
                    continue

                # Quick expand top-left (Q)
                if event.key == pygame.K_q:
                    offset_x -= 4
                    offset_y -= 4
                    ensure_view_within_map()
                    continue

                # Numeric input for -1 tiles
                if event.unicode.isdigit() and basic_tiles[selected_tile][1] == -1:
                    pending_value += event.unicode
                    continue
                if event.key == pygame.K_BACKSPACE:
                    pending_value = pending_value[:-1]
                    continue

                # Zoom
                if event.key == pygame.K_z:
                    TILE_SIZE = min(96, TILE_SIZE + 4)
                    recalc_view_counts_from_window()
                    clear_image_cache()
                    continue
                if event.key == pygame.K_x:
                    TILE_SIZE = max(8, TILE_SIZE - 4)
                    recalc_view_counts_from_window()
                    clear_image_cache()
                    continue

        # DRAW
        screen.fill((12,12,12))

        # draw tiles viewport
        for vy in range(VIEW_HEIGHT):
            for vx in range(VIEW_WIDTH):
                gx = vx + offset_x
                gy = vy + offset_y
                rect = pygame.Rect(vx*TILE_SIZE, vy*TILE_SIZE, TILE_SIZE, TILE_SIZE)

                if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
                    tile = tile_map[gy][gx]
                    ch, num = get_tile_char_num(tile)
                    img = load_tile_image(ch, num, TILE_SIZE)
                    # draw image or error rect
                    if img:
                        screen.blit(img, rect.topleft)
                    else:
                        # should not happen because loader returns error texture, but safe fallback
                        pygame.draw.rect(screen, (255,0,255), rect)

                    stroke = max(1, TILE_SIZE // 16)
                    pygame.draw.rect(screen, (40,40,40), rect, stroke)

                    # draw number always if present
                    if num is not None:
                        font_size = max(10, TILE_SIZE // 2)
                        num_font = pygame.font.SysFont(None, font_size)
                        num_surf = num_font.render(str(num), True, (255,255,255))
                        # small shadow
                        screen.blit(num_surf, (vx*TILE_SIZE + 2, vy*TILE_SIZE + 2))
                else:
                    # area outside map (expansion should prevent this normally)
                    pygame.draw.rect(screen, (20,20,20), rect)
                    pygame.draw.rect(screen, (40,40,40), rect, 1)

        # bottom UI panel
        ui_rect = pygame.Rect(0, SCREEN_HEIGHT - UI_PANEL_HEIGHT, SCREEN_WIDTH, UI_PANEL_HEIGHT)
        pygame.draw.rect(screen, (18,18,18), ui_rect)

        # info + instructions
        used_bbox = compute_used_bbox()
        used_w = used_h = 0
        if used_bbox:
            used_w = used_bbox[2] - used_bbox[0] + 1
            used_h = used_bbox[3] - used_bbox[1] + 1

        info = f"Tile: {selected_tile}{('' if not pending_value else pending_value)}   Used W,H: {used_w},{used_h}   Map size: {MAP_WIDTH}x{MAP_HEIGHT}   Offset: {offset_x},{offset_y}   Tile size: {TILE_SIZE}px"
        instructions = "Arrows / WASD: pan | Left/Right: switch tile | E: eyedropper | Shift+S: save | Shift+L: load | Z/X: zoom | Q: quick expand top-left"
        help_text = info + "    " + instructions
        max_text_w = SCREEN_WIDTH - 16

        wrapped = wrap_text_lines(help_text, base_font, max_text_w)
        text_y = SCREEN_HEIGHT - UI_PANEL_HEIGHT + 6
        for line in wrapped:
            surf = base_font.render(line, True, (220,220,220))
            screen.blit(surf, (8, text_y))
            text_y += base_font.get_linesize()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main_loop()
