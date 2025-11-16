import pygame

# -------------------- CONFIG --------------------
TILE_SIZE = 32
VIEW_WIDTH = 16
VIEW_HEIGHT = 16
MAP_WIDTH = 100   # Large map
MAP_HEIGHT = 100

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

# -------------------- INIT --------------------
pygame.init()
screen = pygame.display.set_mode((VIEW_WIDTH*TILE_SIZE, VIEW_HEIGHT*TILE_SIZE + 32))
pygame.display.set_caption("Tile Editor")
font = pygame.font.SysFont(None, 24)

# Tile map: store as string "tile" or "tile:num"
tile_map = [["-" for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
offset_x, offset_y = 0, 0

tile_keys = list(basic_tiles.keys())
selected_index = 1
selected_tile = tile_keys[selected_index]
pending_value = ""  # For tiles that need a number

dragging = False
paint_tile = selected_tile

clock = pygame.time.Clock()

# -------------------- FUNCTIONS --------------------
def get_used_dimensions():
    min_x, max_x, min_y, max_y = MAP_WIDTH, 0, MAP_HEIGHT, 0
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
        return 0,0
    return max_x - min_x + 1, max_y - min_y + 1

def save_map_text(filename="tilemap.txt"):
    # Compute used area
    min_x, max_x, min_y, max_y = MAP_WIDTH, 0, MAP_HEIGHT, 0
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
        print("Map empty, nothing to save.")
        return

    trimmed_width = max_x - min_x + 1
    trimmed_height = max_y - min_y + 1

    # Save only the used portion with width/height at the top
    with open(filename, "w") as f:
        f.write(f"width = {trimmed_width}\n")
        f.write(f"height = {trimmed_height}\n")
        for y in range(min_y, max_y + 1):
            line = ""
            for x in range(min_x, max_x + 1):
                tile = tile_map[y][x]
                if ":" in tile:
                    char, num = tile.split(":")
                    line += f"{char}{num}"  # no colon
                else:
                    char = tile
                    # Default number for -1 tiles
                    if basic_tiles.get(char, [0, -2])[1] == -1:
                        line += f"{char}0"
                    else:
                        line += char
            f.write(line + "\n")
    print(f"Map saved to {filename} (trimmed to used area)")



def place_tile(gx, gy):
    global tile_map
    if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
        if basic_tiles[selected_tile][1] == -1:
            # Force number; default to 0 if none typed
            val = pending_value if pending_value else "0"
            tile_map[gy][gx] = f"{selected_tile}:{val}"
        else:
            tile_map[gy][gx] = selected_tile

def get_tile_char_num(tile):
    if ":" in tile:
        char, num = tile.split(":")
        return char, num
    # If tile is -1 but no number, default to 0
    if basic_tiles.get(tile, [0,-2])[1] == -1:
        return tile, "0"
    return tile, None

# -------------------- MAIN LOOP --------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Mouse
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            gx = x // TILE_SIZE + offset_x
            gy = y // TILE_SIZE + offset_y
            if event.button == 1:
                place_tile(gx, gy)
                dragging = True
                paint_tile = tile_map[gy][gx]
            elif event.button == 3:
                tile_map[gy][gx] = "-"
                dragging = True
                paint_tile = "-"

        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False

        elif event.type == pygame.MOUSEMOTION and dragging:
            x, y = event.pos
            gx = x // TILE_SIZE + offset_x
            gy = y // TILE_SIZE + offset_y
            place_tile(gx, gy)

        # Keyboard
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                selected_index = (selected_index + 1) % len(tile_keys)
                selected_tile = tile_keys[selected_index]
                pending_value = ""
            elif event.key == pygame.K_LEFT:
                selected_index = (selected_index - 1) % len(tile_keys)
                selected_tile = tile_keys[selected_index]
                pending_value = ""
            elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                save_map_text()
            elif event.key == pygame.K_w:  # up
                offset_y = max(0, offset_y - 1)
            elif event.key == pygame.K_s:  # down
                offset_y = min(MAP_HEIGHT - VIEW_HEIGHT, offset_y + 1)
            elif event.key == pygame.K_a:  # left
                offset_x = max(0, offset_x - 1)
            elif event.key == pygame.K_d:  # right
                offset_x = min(MAP_WIDTH - VIEW_WIDTH, offset_x + 1)
            elif event.key == pygame.K_UP:
                offset_y = max(0, offset_y - 1)
            elif event.key == pygame.K_DOWN:
                offset_y = min(MAP_HEIGHT - VIEW_HEIGHT, offset_y + 1)
            elif event.key == pygame.K_a:
                offset_x = max(0, offset_x - 1)
            elif event.key == pygame.K_d:
                offset_x = min(MAP_WIDTH - VIEW_WIDTH, offset_x + 1)
            elif event.unicode.isdigit() and basic_tiles[selected_tile][1] == -1:
                pending_value += event.unicode
            elif event.key == pygame.K_BACKSPACE:
                pending_value = pending_value[:-1]
            elif event.key == pygame.K_z:
                TILE_SIZE = min(64, TILE_SIZE + 4)
            elif event.key == pygame.K_x:
                TILE_SIZE = max(8, TILE_SIZE - 4)
            # Eyedropper key
            elif event.key == pygame.K_e:
                # Get mouse position
                x, y = pygame.mouse.get_pos()
                gx = x // TILE_SIZE + offset_x
                gy = y // TILE_SIZE + offset_y
                if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
                    tile = tile_map[gy][gx]
                    char, num = get_tile_char_num(tile)
                    selected_tile = char
                    pending_value = num if num else ""
                    # Update selected_index to match selected_tile
                    if char in tile_keys:
                        selected_index = tile_keys.index(char)


    # -------------------- DRAW --------------------
    screen.fill((0,0,0))
    for y in range(VIEW_HEIGHT):
        for x in range(VIEW_WIDTH):
            gx = x + offset_x
            gy = y + offset_y
            if 0 <= gx < MAP_WIDTH and 0 <= gy < MAP_HEIGHT:
                tile = tile_map[gy][gx]
                char, num = get_tile_char_num(tile)
                color = TILE_COLORS.get(char, (255,255,255))
                rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, color, rect)
                # Stroke scales with zoom
                stroke = max(1, TILE_SIZE//16)
                pygame.draw.rect(screen, (50,50,50), rect, stroke)
                # Draw number always if exists
                if num:
                    font_size = max(12, TILE_SIZE//2)
                    num_font = pygame.font.SysFont(None, font_size)
                    num_surf = num_font.render(num, True, (255,255,255))
                    screen.blit(num_surf, (x*TILE_SIZE + 2, y*TILE_SIZE + 2))

    # UI text
    used_w, used_h = get_used_dimensions()
    info_text = f"Tile: {selected_tile}{pending_value if pending_value else ''} | Used W,H: {used_w},{used_h}"
    text_surface = font.render(info_text, True, (255,255,255))
    screen.blit(text_surface, (5, VIEW_HEIGHT*TILE_SIZE + 5))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
