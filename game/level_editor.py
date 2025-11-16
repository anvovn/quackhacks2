#!/usr/bin/env python3
import os
import pygame
import textwrap

# -------------------- CONFIG --------------------
TILE_SIZE = 32

# initial viewport tile counts (will be recalculated on window resize)
VIEW_WIDTH = 16
VIEW_HEIGHT = 16

# initial map size (can expand)
MAP_WIDTH = 100
MAP_HEIGHT = 100

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

UI_PANEL_HEIGHT = 100  # bottom UI area height (wraps text here)

# -------------------- INIT PYGAME --------------------
pygame.init()
# Start with a resizable OS window; user can resize and editor will show more tiles
SCREEN_WIDTH = max(800, VIEW_WIDTH * TILE_SIZE)
SCREEN_HEIGHT = max(600, VIEW_HEIGHT * TILE_SIZE + UI_PANEL_HEIGHT)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Tile Editor")
base_font = pygame.font.SysFont(None, 18)

# -------------------- GLOBAL STATE --------------------
# tile_map stores strings like "-" or "E:3"
tile_map = [["-" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
offset_x = 0
offset_y = 0

tile_keys = list(basic_tiles.keys())
selected_index = 1
selected_tile = tile_keys[selected_index]
pending_value = ""  # number typed for -1 tiles

dragging = False
paint_tile = selected_tile

image_cache = {}  # cached (char, num, tile_size) -> Surface

clock = pygame.time.Clock()
# Load error fallback texture
ERROR_TEXTURE = pygame.image.load("../assets/art/error.png").convert_alpha()

# -------------------- HELPERS: IMAGES --------------------
def tile_image_filename(char, num):
    """Map char and num to a filename in ASSETS_DIR (adjust to your filenames)."""
    # Floors/walls by variant:
    if char == "#":
        return "wood_wall.png" if num == "1" else "concrete_wall.png"
    if char == " ":
        if num == "1":
            return "wood_floor.png"
        if num == "2":
            return "green_carpet.png"
        if num == "3":
            return "tile_floor.png"
        return "concrete_floor.png"
    if char == "*":
        return "duck_player.png"
    if char == "=":
        return "door_templates.png"
    if char == "<":
        return "cardboard_box.png"
    if char == "c":
        return "Chest.png"
    if char == "p":
        return "cardboard_box.png"
    if char == "E":
        # try roomba variants by number or generic fallback
        if num and num.isdigit():
            cand = f"roomba_{num}.png"
            if os.path.exists(os.path.join(ASSETS_DIR, cand)):
                return cand
        if os.path.exists(os.path.join(ASSETS_DIR, "roomba.png")):
            return "roomba.png"
        # fallback to None -> color rect
        return None
    if char in ("^", "v", "@"):
        return "tile_floor.png"
    if char == "?":
        return "door_templates.png"
    return None

def load_tile_image(char, num, tile_size):
    key = (char, num, tile_size)
    if key in image_cache:
        return image_cache[key]
    fname = tile_image_filename(char, num)
    surf = None
    if fname:
        path = os.path.join(ASSETS_DIR, fname)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.smoothscale(img, (tile_size, tile_size))
                surf = img
            except Exception:
                surf = None
    image_cache[key] = surf
    return surf

def clear_image_cache():
    image_cache.clear()

# -------------------- HELPERS: MAP EXPANSION --------------------
def expand_map_to_include(gx, gy):
    """
    Expand tile_map (mutates global MAP_WIDTH/MAP_HEIGHT and tile_map) so that tile coords (gx,gy) exist.
    This uses the 'A' behavior (add empty rows/cols BEFORE existing content when negative).
    It also adjusts offset_x/offset_y so the camera continues to point at same world cells.
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
        new_width = MAP_WIDTH + add_left + add_right
        new_height = MAP_HEIGHT + add_top + add_bottom

        # create new blank map
        new_map = [["-" for _ in range(new_width)] for _ in range(new_height)]

        # copy old data into shifted position (add_top, add_left)
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                new_map[y + add_top][x + add_left] = tile_map[y][x]

        tile_map = new_map
        MAP_WIDTH = new_width
        MAP_HEIGHT = new_height

        # adjust offsets: if we added left/top, shift camera by that amount
        offset_x += add_left
        offset_y += add_top

# Ensure the viewport stays backed by a valid region, expanding map if necessary.
def ensure_view_within_map():
    global offset_x, offset_y
    # If view extends left/top < 0, expand accordingly
    if offset_x < 0 or offset_y < 0:
        expand_map_to_include(offset_x, offset_y)
    # If view extends beyond right/bottom, expand accordingly
    if offset_x + VIEW_WIDTH > MAP_WIDTH or offset_y + VIEW_HEIGHT > MAP_HEIGHT:
        expand_map_to_include(offset_x + VIEW_WIDTH - 1, offset_y + VIEW_HEIGHT - 1)

# -------------------- HELPERS: TILE FORMAT --------------------
def get_tile_char_num(tile):
    """Return (char, num or None). If tile char expects number but none stored, default to '0' for display."""
    if ":" in tile:
        char, num = tile.split(":", 1)
        return char, num
    if basic_tiles.get(tile, [0, -2])[1] == -1:
        return tile, "0"
    return tile, None

def get_tile_surface(tile_char, tile_num):
    try:
        # Get atlas for tile
        atlas = TILE_ATLAS.get(tile_char)
        if atlas is None:
            return ERROR_TEXTURE

        # If the tile uses numbered sub-tiles (floor types, wood/concrete, etc.)
        if tile_num is not None:
            tile_num = int(tile_num)
            atlas_height = atlas.get_height() // TILE_SIZE
            if tile_num < 0 or tile_num >= atlas_height:
                print(f"[ART ERROR] invalid index {tile_num} for tile '{tile_char}'")
                return ERROR_TEXTURE
            # Return the correct subsurface row
            return atlas.subsurface(
                pygame.Rect(0, tile_num * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            )

        # Else use atlas directly
        return atlas

    except Exception as e:
        print(f"[ART ERROR] '{tile_char}{tile_num}' failed: {e}")
        return ERROR_TEXTURE


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
    trimmed_width = max_x - min_x + 1
    trimmed_height = max_y - min_y + 1

    with open(filename, "w") as f:
        f.write(f"width = {trimmed_width}\n")
        f.write(f"height = {trimmed_height}\n")
        for y in range(min_y, max_y + 1):
            line = ""
            for x in range(min_x, max_x + 1):
                tile = tile_map[y][x]
                if ":" in tile:
                    char, num = tile.split(":", 1)
                    line += f"{char}{num}"
                else:
                    char = tile
                    if basic_tiles.get(char, [0, -2])[1] == -1:
                        line += f"{char}0"
                    else:
                        line += char
            f.write(line + "\n")
    print(f"Map saved to {filename} (trimmed {trimmed_width}x{trimmed_height})")

def parse_map_line_to_row(line):
    """Parse a single map line like 'E3# 10' -> ['E:3','#',' ', '1','0'?]. Actually parse digits after chars."""
    row = []
    i = 0
    while i < len(line):
        ch = line[i]
        i += 1
        if ch == "\n":
            break
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

    # parse optional header lines
    idx = 0
    file_w = file_h = None
    while idx < len(lines):
        ln = lines[idx].strip()
        if ln.startswith("width"):
            try:
                file_w = int(ln.split("=")[1].strip())
                idx += 1
                continue
            except Exception:
                file_w = None
        if ln.startswith("height"):
            try:
                file_h = int(ln.split("=")[1].strip())
                idx += 1
                continue
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

    # Auto-expand map to fit loaded file (choice 4: C)
    if new_w > MAP_WIDTH or new_h > MAP_HEIGHT:
        # increase width/height by adding columns on the right and rows on the bottom
        for row in tile_map:
            row.extend(["-"] * (new_w - MAP_WIDTH))
        for _ in range(new_h - MAP_HEIGHT):
            tile_map.append(["-"] * new_w)
        MAP_WIDTH = max(MAP_WIDTH, new_w)
        MAP_HEIGHT = max(MAP_HEIGHT, new_h)

    # ensure map has at least new_w per row
    for y in range(MAP_HEIGHT):
        if len(tile_map[y]) < new_w:
            tile_map[y].extend(["-"] * (new_w - len(tile_map[y])))

    # copy rows into top-left
    for y, r in enumerate(rows):
        for x, t in enumerate(r):
            tile_map[y][x] = t

    # reset camera to top-left of loaded map
    offset_x = 0
    offset_y = 0
    clear_image_cache()
    print(f"Loaded {filename} into editor (size {new_w}x{new_h})")

# -------------------- PLACEMENT --------------------
def place_tile_at(gx, gy):
    expand_map_to_include(gx, gy)
    if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
        if basic_tiles[selected_tile][1] == -1:
            val = pending_value if pending_value else "0"
            tile_map[gy][gx] = f"{selected_tile}:{val}"
        else:
            tile_map[gy][gx] = selected_tile

# -------------------- UI WRAP --------------------
def wrap_text_lines(text, font, max_width):
    """Return a list of wrapped lines that fit in max_width using font.size for width measurement."""
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
            # If single word longer than width, forcibly split with textwrap by characters
            if font.size(w)[0] > max_width:
                # break w into chunks that fit
                chars = list(w)
                chunk = ""
                for ch in chars:
                    if font.size(chunk + ch)[0] <= max_width:
                        chunk += ch
                    else:
                        if chunk:
                            lines.append(chunk)
                        chunk = ch
                if chunk:
                    cur = chunk
                else:
                    cur = ""
            else:
                cur = w
    if cur:
        lines.append(cur)
    return lines

# -------------------- WINDOW / VIEWPORT --------------------
def recalc_view_counts_from_window():
    global VIEW_WIDTH, VIEW_HEIGHT
    # available drawable area excludes bottom UI panel
    avail_w = max(64, SCREEN_WIDTH)
    avail_h = max(64, SCREEN_HEIGHT - UI_PANEL_HEIGHT)
    VIEW_WIDTH = max(4, avail_w // TILE_SIZE)
    VIEW_HEIGHT = max(3, avail_h // TILE_SIZE)

# -------------------- MAIN LOOP --------------------
def main_loop():
    global SCREEN_WIDTH, SCREEN_HEIGHT, screen
    global TILE_SIZE, VIEW_WIDTH, VIEW_HEIGHT, offset_x, offset_y
    global dragging, paint_tile, selected_index, selected_tile, pending_value

    running = True
    recalc_view_counts_from_window()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # window resized -> update viewport tile counts
            elif event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                recalc_view_counts_from_window()
                clear_image_cache()

            # mouse
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # ignore clicks in UI panel
                if my >= SCREEN_HEIGHT - UI_PANEL_HEIGHT:
                    continue
                gx = mx // TILE_SIZE + offset_x
                gy = my // TILE_SIZE + offset_y
                if event.button == 1:
                    place_tile_at(gx, gy)
                    dragging = True
                    paint_tile = tile_map[gy][gx]
                elif event.button == 3:
                    # erase (expand to include in case clicking outside)
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

            # keyboard
            elif event.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods()

                # save (Shift+S)
                if event.key == pygame.K_s and (mods & pygame.KMOD_SHIFT):
                    save_map_text()
                    continue

                # load (Shift+L)
                if event.key == pygame.K_l and (mods & pygame.KMOD_SHIFT):
                    load_map_text("tilemap.txt")
                    continue

                # eyedropper (E)
                if event.key == pygame.K_e:
                    mx, my = pygame.mouse.get_pos()
                    if my >= SCREEN_HEIGHT - UI_PANEL_HEIGHT:
                        continue
                    gx = mx // TILE_SIZE + offset_x
                    gy = my // TILE_SIZE + offset_y
                    expand_map_to_include(gx, gy)
                    if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
                        tile = tile_map[gy][gx]
                        char, num = get_tile_char_num(tile)
                        selected_tile = char
                        pending_value = num if num else ""
                        if char in tile_keys:
                            selected_index = tile_keys.index(char)
                    continue

                # tile switching left/right
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

                # panning: WASD and arrow keys
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

                # quick expand top-left: Q (adds space by moving offset negative, ensure_view will expand)
                if event.key == pygame.K_q:
                    offset_x -= 4
                    offset_y -= 4
                    ensure_view_within_map()
                    continue

                # numerics for tile types that need a number
                if event.unicode.isdigit() and basic_tiles[selected_tile][1] == -1:
                    pending_value += event.unicode
                    continue
                if event.key == pygame.K_BACKSPACE:
                    pending_value = pending_value[:-1]
                    continue

                # zoom
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

        # draw tile viewport (only the visible region)
        for vy in range(VIEW_HEIGHT):
            for vx in range(VIEW_WIDTH):
                gx = vx + offset_x
                gy = vy + offset_y
                rect = pygame.Rect(vx*TILE_SIZE, vy*TILE_SIZE, TILE_SIZE, TILE_SIZE)

                if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
                    tile = tile_map[gy][gx]
                    char, num = get_tile_char_num(tile)
                    img = load_tile_image(char, num, TILE_SIZE)
                    if img:
                        screen.blit(img, rect.topleft)
                    else:
                        surf = get_tile_surface(char, num)
                        if surf:
                            screen.blit(surf, (x*TILE_SIZE, y*TILE_SIZE))
                        else:
                            pygame.draw.rect(screen, (255,0,255), rect)  # backup fallback

                    stroke = max(1, TILE_SIZE // 16)
                    pygame.draw.rect(screen, (40,40,40), rect, stroke)

                    # draw number always if present (num is None or "0")
                    if num is not None:
                        font_size = max(10, TILE_SIZE // 2)
                        num_font = pygame.font.SysFont(None, font_size)
                        num_surf = num_font.render(str(num), True, (255,255,255))
                        # shadow for readability
                        screen.blit(num_surf, (vx*TILE_SIZE + 2, vy*TILE_SIZE + 2))
                else:
                    # region outside current map (should rarely occur because we expand)
                    pygame.draw.rect(screen, (20,20,20), rect)
                    pygame.draw.rect(screen, (40,40,40), rect, 1)

        # draw bottom UI panel background
        ui_rect = pygame.Rect(0, SCREEN_HEIGHT - UI_PANEL_HEIGHT, SCREEN_WIDTH, UI_PANEL_HEIGHT)
        pygame.draw.rect(screen, (18,18,18), ui_rect)

        # UI text lines (wrap based on available width)
        used_bbox = compute_used_bbox()
        used_w = used_h = 0
        if used_bbox:
            used_w = used_bbox[2] - used_bbox[0] + 1
            used_h = used_bbox[3] - used_bbox[1] + 1

        info = f"Tile: {selected_tile}{('' if not pending_value else pending_value)}    Used W,H: {used_w},{used_h}    Map size: {MAP_WIDTH}x{MAP_HEIGHT}    Offset: {offset_x},{offset_y}    Tile size: {TILE_SIZE}px"
        instructions = "Arrows / WASD: pan | Left/Right: switch tile | E: eyedropper | Shift+S: save | Shift+L: load | Z/X: zoom | Q: quick expand top-left"
        help_text = info + "    " + instructions
        max_text_w = SCREEN_WIDTH - 16  # padding

        wrapped = wrap_text_lines(help_text, base_font, max_text_w)
        # draw multiple lines starting near bottom panel top + small padding
        text_y = SCREEN_HEIGHT - UI_PANEL_HEIGHT + 6
        for line in wrapped:
            surf = base_font.render(line, True, (220,220,220))
            screen.blit(surf, (8, text_y))
            text_y += base_font.get_linesize()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main_loop()
