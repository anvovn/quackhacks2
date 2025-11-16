import pygame, os

# -------------------- CONFIG --------------------
TILE_SIZE = 32
VIEW_WIDTH = 16
VIEW_HEIGHT = 16
MAP_WIDTH = 100
MAP_HEIGHT = 100

basic_tiles = {
    "-":[0,-2],
    "#":[1,-1],
    " ":[2,-1],
    "*":[3,-2],
    "=":[9,-1],
    "<":[8,-1],
    "?":[7,-1],
    "E":[0,-1],
    "^":[11,-1],
    "v":[12,-1],
    "@":[13,-1],
    "c":[21,-1],
    "p":[22,-1]
}

TILE_COLORS = {
    "-": (255,255,255),
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

# -------------------- PYGAME INIT --------------------
pygame.init()
screen = pygame.display.set_mode((VIEW_WIDTH*TILE_SIZE, VIEW_HEIGHT*TILE_SIZE + 48))
pygame.display.set_caption("Tile Editor")
font = pygame.font.SysFont(None, 22)
clock = pygame.time.Clock()


# ----------------------------------------------------
# ART LOADING + ERROR TEXTURE
# ----------------------------------------------------
ART_PATH = "../assets/art"

def make_error_texture():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill((255, 0, 255))  # bright error magenta
    return surf

error_img = make_error_texture()

def load_img(name):
    path = os.path.join(ART_PATH, name)
    try:
        img = pygame.image.load(path).convert_alpha()
        return img
    except:
        print(f"[ART ERROR] Could not load: {name}")
        return error_img

# numbered variations
FLOOR_IMAGES = {
    0: load_img("concrete_floor.png"),
    1: load_img("wood_floor.png"),
    2: load_img("green_carpet.png"),
    3: load_img("tile_floor.png"),
}

WALL_IMAGES = {
    0: load_img("concrete_wall.png"),
    1: load_img("wood_wall.png")
}

ENEMY_IMAGES = {
    0: load_img("passive_roomba.png"),
    1: load_img("search_roomba.png"),
    2: load_img("attack_roomba.png")
}

def get_tile_image(char, num):
    """Return correct art OR None if tile uses colored rectangles."""
    if char == " ":
        return FLOOR_IMAGES.get(num, error_img)
    if char == "#":
        return WALL_IMAGES.get(num, error_img)
    if char == "E":
        return ENEMY_IMAGES.get(num, error_img)
    return None  # everything else = use colored rectangles


# -------------------- MAP STORAGE --------------------
tile_map = [["-" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

offset_x, offset_y = 0, 0
selected_index = 1
tile_keys = list(basic_tiles.keys())
selected_tile = tile_keys[selected_index]
pending_value = ""

dragging = False


# -------------------- FILE LOADING --------------------
def load_map_text(filename):
    global tile_map, MAP_WIDTH, MAP_HEIGHT
    try:
        with open(filename, "r") as f:
            lines = f.read().splitlines()
    except:
        print("[LOAD ERROR] Cannot open", filename)
        return

    # header
    if not lines[0].startswith("width") or not lines[1].startswith("height"):
        print("[LOAD ERROR] No correct header")
        return

    width = int(lines[0].split("=")[1])
    height = int(lines[1].split("=")[1])

    MAP_WIDTH = max(width, MAP_WIDTH)
    MAP_HEIGHT = max(height, MAP_HEIGHT)

    new_map = [["-" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]

    row = 0
    for line in lines[2:]:
        col = 0
        i = 0
        while i < len(line):
            c = line[i]
            if c in basic_tiles:
                if basic_tiles[c][1] == -1:
                    # has number
                    j = i+1
                    num_str = ""
                    while j < len(line) and line[j].isdigit():
                        num_str += line[j]
                        j += 1
                    if num_str == "":
                        num_str = "0"
                    new_map[row][col] = f"{c}:{num_str}"
                    i = j
                else:
                    new_map[row][col] = c
                    i += 1
                col += 1
            else:
                i += 1
        row += 1
        if row >= MAP_HEIGHT:
            break

    tile_map[:] = new_map
    print(f"[LOAD] Loaded {filename}")


# -------------------- SAVE --------------------
def get_used_dimensions():
    min_x, max_x = MAP_WIDTH, 0
    min_y, max_y = MAP_HEIGHT, 0
    used = False

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if tile_map[y][x] != "-":
                used = True
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    if not used:
        return 0, 0
    return max_x-min_x+1, max_y-min_y+1


def save_map_text(filename="tilemap.txt"):
    min_x, max_x = MAP_WIDTH, 0
    min_y, max_y = MAP_HEIGHT, 0
    used = False

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if tile_map[y][x] != "-":
                used = True
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    if not used:
        print("[SAVE] Map empty")
        return

    w = max_x-min_x+1
    h = max_y-min_y+1

    with open(filename, "w") as f:
        f.write(f"width = {w}\n")
        f.write(f"height = {h}\n")
        for y in range(min_y, max_y+1):
            line = ""
            for x in range(min_x, max_x+1):
                tile = tile_map[y][x]
                if ":" in tile:
                    c, num = tile.split(":")
                    line += f"{c}{num}"
                else:
                    if basic_tiles[tile][1] == -1:
                        line += f"{tile}0"
                    else:
                        line += tile
            f.write(line + "\n")

    print("[SAVE] Saved", filename)


# -------------------- TILE HELPERS --------------------
def get_tile_char_num(tile):
    if ":" in tile:
        c, num = tile.split(":")
        return c, num
    if basic_tiles.get(tile, [0,-2])[1] == -1:
        return tile, "0"
    return tile, None


def place_tile(gx, gy):
    if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
        if basic_tiles[selected_tile][1] == -1:
            val = pending_value if pending_value else "0"
            tile_map[gy][gx] = f"{selected_tile}:{val}"
        else:
            tile_map[gy][gx] = selected_tile


# -------------------- MAIN LOOP --------------------
running = True
while running:

    # ---------- EVENTS ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- mouse ---
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            gx = mx // TILE_SIZE + offset_x
            gy = my // TILE_SIZE + offset_y
            if event.button == 1:
                place_tile(gx, gy)
                dragging = True
            elif event.button == 3:
                tile_map[gy][gx] = "-"
                dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False

        elif event.type == pygame.MOUSEMOTION and dragging:
            mx, my = event.pos
            gx = mx // TILE_SIZE + offset_x
            gy = my // TILE_SIZE + offset_y
            place_tile(gx, gy)

        # --- keyboard ---
        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_RIGHT:
                selected_index = (selected_index + 1) % len(tile_keys)
                selected_tile = tile_keys[selected_index]
                pending_value = ""

            elif event.key == pygame.K_LEFT:
                selected_index = (selected_index - 1) % len(tile_keys)
                selected_tile = tile_keys[selected_index]
                pending_value = ""

            elif event.key == pygame.K_w:
                offset_y = max(0, offset_y - 1)
            elif event.key == pygame.K_s:
                offset_y = min(MAP_HEIGHT - VIEW_HEIGHT, offset_y + 1)
            elif event.key == pygame.K_a:
                offset_x = max(0, offset_x - 1)
            elif event.key == pygame.K_d:
                offset_x = min(MAP_WIDTH - VIEW_WIDTH, offset_x + 1)

            elif event.unicode.isdigit() and basic_tiles[selected_tile][1] == -1:
                pending_value += event.unicode

            elif event.key == pygame.K_BACKSPACE:
                pending_value = pending_value[:-1]

            elif event.key == pygame.K_z:   # zoom in
                TILE_SIZE = min(64, TILE_SIZE + 4)
            elif event.key == pygame.K_x:   # zoom out
                TILE_SIZE = max(8, TILE_SIZE - 4)

            elif event.key == pygame.K_e:  # eyedropper
                mx, my = pygame.mouse.get_pos()
                gx = mx // TILE_SIZE + offset_x
                gy = my // TILE_SIZE + offset_y
                if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
                    tile = tile_map[gy][gx]
                    c, num = get_tile_char_num(tile)
                    selected_tile = c
                    pending_value = num or ""
                    selected_index = tile_keys.index(c)

            elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                save_map_text()

            elif event.key == pygame.K_l and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                load_map_text("tilemap.txt")


    # ---------- DRAW ----------
    screen.fill((0,0,0))

    for vy in range(VIEW_HEIGHT):
        for vx in range(VIEW_WIDTH):
            gx = vx + offset_x
            gy = vy + offset_y

            if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
                tile = tile_map[gy][gx]
                c, num = get_tile_char_num(tile)

                rect = pygame.Rect(vx*TILE_SIZE, vy*TILE_SIZE, TILE_SIZE, TILE_SIZE)

                # draw art if available
                img = None
                if num is not None:
                    try:
                        num_int = int(num)
                    except:
                        num_int = -1
                    img = get_tile_image(c, num_int)

                if img:
                    scaled = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                    screen.blit(scaled, rect.topleft)
                else:
                    color = TILE_COLORS.get(c, (255,255,255))
                    pygame.draw.rect(screen, color, rect)

                # draw border
                pygame.draw.rect(screen, (50,50,50), rect, max(1, TILE_SIZE//16))

                # draw number
                if num:
                    f = pygame.font.SysFont(None, max(12, TILE_SIZE//2))
                    surf = f.render(num, True, (255,255,255))
                    screen.blit(surf, (vx*TILE_SIZE + 2, vy*TILE_SIZE + 2))

    # UI row
    used_w, used_h = get_used_dimensions()
    ui_text = f"Tile: {selected_tile}{pending_value}  |  Used: {used_w}x{used_h}  |  SHIFT+S Save  SHIFT+L Load"
    ui_surf = font.render(ui_text, True, (255,255,255))
    screen.blit(ui_surf, (4, VIEW_HEIGHT*TILE_SIZE + 8))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
