
#NEON RIFT: THE LAST GUARDIAN

from math import acos, cos, sin, radians, sqrt, atan2, degrees
import time
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *



WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 760
window_width = WINDOW_WIDTH
window_height = WINDOW_HEIGHT
CELL = 200.0
PLAYER_RADIUS = 30.0
GRAVITY = 980.0
JUMP_SPEED = 430.0
STANDING_EYE_HEIGHT = 145.0
SITTING_EYE_HEIGHT = 82.0
WALK_SPEED = 360.0
SITTING_SPEED = 190.0
WORLD_VIEW_CELLS = 9
KEY_FALLBACK_TIMEOUT = 0.68
MOVE_RESPONSE = 10.5
TURN_RESPONSE = 13.0

# Visual tuning constants.
SKY_TOP_COLOR = (0.004, 0.009, 0.030)
SKY_HORIZON_COLOR = (0.045, 0.105, 0.165)
FOG_COLOR = (0.045, 0.095, 0.135, 1.0)
FOG_START = 980.0
FOG_END = 2550.0
TERRAIN_BASE_COLOR = (0.105, 0.165, 0.145)
TERRAIN_ALT_COLOR = (0.135, 0.205, 0.170)
CYAN_COLOR = (0.10, 0.90, 1.0)
MAGENTA_COLOR = (0.86, 0.10, 1.0)
DANGER_COLOR = (1.0, 0.20, 0.06)
BIRD_COLOR = (0.62, 0.76, 0.90)
WEAPON_FORWARD_OFFSET = 118.0
WEAPON_VERTICAL_OFFSET = 62.0
MAX_PARTICLES = 120
MAX_FLOATING_TEXTS = 12
ENERGY_REQUIRED = 3
CORE_MAX_HEALTH = 100
GRID_MAX_INTEGRITY = 100
MISSED_SHOT_DAMAGE = 4
INITIAL_ACTIVE_ENEMIES = 10
MAX_ACTIVE_ENEMIES = 20
ENEMY_TURN_SPEED = 235.0
ENEMY_ATTACK_ANIMATION_DURATION = 0.54
RIFT_ANCHOR_MAX_HEALTH = 5
ANCHOR_PROJECTILE_DAMAGE = 14
EMP_MAX_CHARGES = 3
EMP_RADIUS = 580.0
EMP_STUN_DURATION = 3.6
EMP_COOLDOWN = 8.0
SENTRY_MAX_CHARGES = 2
SENTRY_LIFETIME = 48.0
SENTRY_RANGE = 760.0
CORE_UPLOAD_DURATION = 24.0
CORE_UPLOAD_RADIUS = 520.0

# Map symbols:
# # = solid boundary/building wall
# . = walkable ground or destroyed road
# f = fallen building/debris
# r = rubble
# t = tree or vegetation obstacle
# h = environmental hazard
# e = enemy spawn point
# k = energy crystal
# c = fixed Aether Grid Core
# b = bridge or special crossing
# p = player start position

OPEN_ROW = "#" + "." * 39 + "#"
MAP_LAYOUT = [
    "#########################################",
    "#.........#.........#.........#......e..#",
    "#.........#.........#.........#.........#",
    "#..fff....#.........#...fff...#.........#",
    "#..fff....#..rrr....#...fff...#....e....#",
    OPEN_ROW,
    "#....t....#....h....#.........#..rrr....#",
    "#....t....#.........#.........#..rrr....#",
    "#.........#..fff....#....k....#.........#",
    OPEN_ROW,
    "#..rrr....#..fff....#.........#....t....#",
    "#.........#.........#....h....#....t....#",
    "#.........#....c....#.........#.........#",
    "#" + "." * 14 + "p" + "." * 24 + "#",
    "#....e....#..rrr....#...fff...#.........#",
    "#....t....#.........#...fff...#....k....#",
    "#.........#.........#.........#.........#",
    "#.........#..rrr....#....b....#..fff....#",
    "#..e......#.........#....h....#.........#",
    OPEN_ROW,
    "#..fff....#.........#....t....#.........#",
    "#.........#....k....#.........#...fff...#",
    OPEN_ROW,
    "#.........#.........#.........#.........#",
    "#########################################",
]

# the player's starting cell.
EXTRA_ENEMY_CELLS = (
    (21, 25), (20, 34), (18, 16), (17, 27),
    (15, 18), (12, 13), (12, 17), (10, 24),
    (8, 27), (7, 3), (4, 16), (2, 33),
)
ROAD_ROWS = {5, 9, 13, 19, 22}
MAP_H = len(MAP_LAYOUT)
MAP_W = len(MAP_LAYOUT[0])
WORLD_W = MAP_W * CELL
WORLD_H = MAP_H * CELL
SOLID_CELLS = {"#", "f", "r", "t"}

grid = []
player_start = (0.0, 0.0)
core_position = (0.0, 0.0)
enemy_spawn_points = []
crystal_positions = []
bridge_position = (0.0, 0.0)
decorations_by_cell = {}
rift_cells = set()
tree_obstacles = []


def world_from_cell(row, col):
    x = (col + 0.5) * CELL - WORLD_W / 2.0
    y = WORLD_H / 2.0 - (row + 0.5) * CELL
    return x, y


def build_map():
    global grid, player_start, core_position, enemy_spawn_points
    global crystal_positions, bridge_position, decorations_by_cell, rift_cells
    global tree_obstacles

    if any(len(row) != MAP_W for row in MAP_LAYOUT):
        raise ValueError("Every MAP_LAYOUT row must have the same width")
    grid = [list(row) for row in MAP_LAYOUT]
    enemy_spawn_points = []
    crystal_positions = []
    decorations_by_cell = {}
    rift_cells = set()
    tree_obstacles = []

    for row in range(MAP_H):
        for col in range(MAP_W):
            symbol = grid[row][col]
            position = world_from_cell(row, col)
            if symbol == "p":
                player_start = position
                grid[row][col] = "."
            elif symbol == "c":
                core_position = position
                grid[row][col] = "."
            elif symbol == "e":
                enemy_spawn_points.append(position)
                grid[row][col] = "."
            elif symbol == "k":
                crystal_positions.append(position)
                grid[row][col] = "."
            elif symbol == "b":
                bridge_position = position
                grid[row][col] = "."

    for row, col in EXTRA_ENEMY_CELLS:
        if 0 < row < MAP_H - 1 and 0 < col < MAP_W - 1:
            if grid[row][col] == ".":
                enemy_spawn_points.append(world_from_cell(row, col))

    for row in range(1, MAP_H - 1):
        for col in range(1, MAP_W - 1):
            if grid[row][col] != ".":
                continue
            x, y = world_from_cell(row, col)
            if sqrt((x - player_start[0]) ** 2 + (y - player_start[1]) ** 2) < 390.0:
                continue
            code = (row * 37 + col * 61) % 43
            offset_x = ((row * 29 + col * 11) % 91) - 45.0
            offset_y = ((row * 17 + col * 31) % 91) - 45.0
            items = []

            adjacent_solids = []
            for delta_row, delta_col, direction_x, direction_y in (
                    (-1, 0, 0.0, 1.0), (1, 0, 0.0, -1.0),
                    (0, -1, -1.0, 0.0), (0, 1, 1.0, 0.0)):
                neighbor = grid[row + delta_row][col + delta_col]
                if neighbor in SOLID_CELLS:
                    adjacent_solids.append((direction_x, direction_y))

            tree_code = (row * 19 + col * 47) % 31
            if adjacent_solids and row not in ROAD_ROWS and tree_code in (1, 5, 9, 14, 21, 27):
                direction_x, direction_y = adjacent_solids[tree_code % len(adjacent_solids)]
                lateral_x, lateral_y = -direction_y, direction_x
                lateral_offset = ((row * 13 + col * 7) % 61) - 30.0
                tree_x = x + direction_x * 57.0 + lateral_x * lateral_offset
                tree_y = y + direction_y * 57.0 + lateral_y * lateral_offset
                tree_scale = 0.58 + ((row * 5 + col * 3) % 5) * 0.065
                protected_positions = (
                    [player_start, core_position, bridge_position]
                    + crystal_positions + enemy_spawn_points
                )
                is_safe = all(
                    (tree_x - target_x) ** 2 + (tree_y - target_y) ** 2 > 175.0 ** 2
                    for target_x, target_y in protected_positions
                )
                if is_safe:
                    items.append({
                        "type": "tree", "x": tree_x, "y": tree_y,
                        "scale": tree_scale,
                        "rotation": float((row * 23 + col * 41) % 360),
                        "variation": ((row * 11 + col * 17) % 7) / 7.0,
                    })
                    tree_obstacles.append((tree_x, tree_y, 15.0 * tree_scale))

            if not items:
                if code in (2, 19):
                    items.append({
                        "type": "rock", "x": x + offset_x, "y": y + offset_y,
                        "scale": 0.65 + (code % 3) * 0.15,
                    })
                elif code == 7:
                    items.append({
                        "type": "shard", "x": x + offset_x, "y": y + offset_y,
                        "scale": 0.75,
                    })
                elif code == 13:
                    items.append({
                        "type": "dead_plant", "x": x + offset_x,
                        "y": y + offset_y, "scale": 0.8,
                    })
                elif code == 31:
                    items.append({
                        "type": "debris", "x": x + offset_x,
                        "y": y + offset_y, "scale": 0.8,
                    })

            grass_code = (row * 31 + col * 13) % 23
            if row not in ROAD_ROWS and grass_code in (3, 8, 16):
                items.append({
                    "type": "grass", "x": x - offset_x * 0.65,
                    "y": y - offset_y * 0.65,
                    "scale": 0.7 + (grass_code % 3) * 0.12,
                })

            if items:
                decorations_by_cell.setdefault((row, col), []).extend(items)
            if (row * 23 + col * 17) % 47 == 0:
                rift_cells.add((row, col))


def cell_at_world(x, y):
    row, col = cell_indices_from_world(x, y)
    if row < 0 or row >= MAP_H or col < 0 or col >= MAP_W:
        return "#"
    return grid[row][col]

def cell_indices_from_world(x, y):
    col = int((x + WORLD_W / 2.0) // CELL)
    row = int((WORLD_H / 2.0 - y) // CELL)
    return row, col

def trap_extension(row, col):
    cycle = (elapsed_game_time * 0.52 + row * 0.17 + col * 0.11) % 1.0
    if cycle < 0.16 or cycle >= 0.84:
        return 0.0
    if cycle < 0.31:
        amount = (cycle - 0.16) / 0.15
        return amount * amount * (3.0 - 2.0 * amount)
    if cycle < 0.66:
        return 1.0
    amount = (cycle - 0.66) / 0.18
    amount = max(0.0, min(1.0, amount))
    return 1.0 - amount * amount * (3.0 - 2.0 * amount)


def build_navigation_field(target_x, target_y):
    global navigation_field_cache
    target_row, target_col = cell_indices_from_world(target_x, target_y)
    key = (target_row, target_col)
    if key in navigation_field_cache:
        return navigation_field_cache[key]
    if not (0 <= target_row < MAP_H and 0 <= target_col < MAP_W):
        return {}
    if grid[target_row][target_col] in SOLID_CELLS:
        return {}
    if len(navigation_field_cache) >= 4:
        navigation_field_cache = {}

    field = {(target_row, target_col): (target_row, target_col)}
    queue = [(target_row, target_col)]
    queue_index = 0
    while queue_index < len(queue):
        row, col = queue[queue_index]
        queue_index += 1
        for next_row, next_col in (
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1)):
            if not (0 <= next_row < MAP_H and 0 <= next_col < MAP_W):
                continue
            if (next_row, next_col) in field:
                continue
            if grid[next_row][next_col] in SOLID_CELLS:
                continue
            field[(next_row, next_col)] = (row, col)
            queue.append((next_row, next_col))

    navigation_field_cache[key] = field
    return field

def navigation_waypoint(start_x, start_y, target_x, target_y):
    field = build_navigation_field(target_x, target_y)
    start_cell = cell_indices_from_world(start_x, start_y)
    next_cell = field.get(start_cell)
    if next_cell is None or next_cell == start_cell:
        return target_x, target_y
    return world_from_cell(*next_cell)

def is_blocked(x, y):
    sample_points = [
        (x, y),
        (x - PLAYER_RADIUS, y),
        (x + PLAYER_RADIUS, y),
        (x, y - PLAYER_RADIUS),
        (x, y + PLAYER_RADIUS),
    ]
    if any(cell_at_world(px, py) in SOLID_CELLS for px, py in sample_points):
        return True
    return any(
        (x - tree_x) ** 2 + (y - tree_y) ** 2
        < (PLAYER_RADIUS + tree_radius) ** 2
        for tree_x, tree_y, tree_radius in tree_obstacles
    )

def projectile_hits_tree(x, y):
    return any(
        (x - tree_x) ** 2 + (y - tree_y) ** 2 < (tree_radius + 4.0) ** 2
        for tree_x, tree_y, tree_radius in tree_obstacles
    )


# Game state
player_x = 0.0
player_y = 0.0
player_z = 0.0
vertical_velocity = 0.0
player_yaw = 0.0
player_pitch = 0.0
is_grounded = True
is_sitting = False
player_health = 100
player_lives = 3
player_score = 0
elapsed_game_time = 0.0
damage_cooldown = 0.0
core_damage_cooldown = 0.0
checkpoint_x = 0.0
checkpoint_y = 0.0
energy_collected = 0
core_activated = False
core_upload_active = False
core_upload_progress = 0.0
core_health = CORE_MAX_HEALTH
grid_integrity = GRID_MAX_INTEGRITY
missed_shots = 0
ending_choice = None
game_state = "playing"  
status_message = "Protect the Grid Core and recover ECHO's memory crystals."
status_message_timer = 6.0
bullets = []
enemy_projectiles = []
enemies = []
crystals = []
rift_anchors = []
sentries = []
particles = []
floating_texts = []
quadric = None
last_frame_time = 0.0
held_keys = set()
held_special_keys = set()
key_activity_until = {}
special_activity_until = {}
weapon_bob_phase = 0.0
movement_intensity = 0.0
weapon_sway = 0.0
weapon_recoil = 0.0
muzzle_flash_timer = 0.0
hit_marker_timer = 0.0
damage_flash_timer = 0.0
camera_shake_timer = 0.0
forward_velocity = 0.0
turn_velocity = 0.0
pitch_velocity = 0.0
enemy_spawn_timer = 5.0
enemy_spawn_cursor = 0
navigation_field_cache = {}
key_up_callbacks_enabled = False
emp_charges = EMP_MAX_CHARGES
emp_cooldown = 0.0
emp_effect_timer = 0.0
emp_origin_x = 0.0
emp_origin_y = 0.0
sentry_charges = SENTRY_MAX_CHARGES


def set_status(message, duration=3.0):
    global status_message, status_message_timer
    status_message = message
    status_message_timer = duration

def anchors_destroyed_count():
    return sum(1 for anchor in rift_anchors if not anchor["active"])

def create_enemy(spawn_index):
    x, y = enemy_spawn_points[spawn_index % len(enemy_spawn_points)]
    stage_pressure = anchors_destroyed_count() * 0.08
    pressure = 1.0 + min(0.58, elapsed_game_time / 155.0) + stage_pressure
    is_brute = spawn_index % 5 == 4
    max_health = 3 if is_brute else 2
    if elapsed_game_time > 95.0 and spawn_index % 4 == 0:
        max_health += 1
    return {
        "x": x,
        "y": y,
        "health": max_health,
        "max_health": max_health,
        "speed": (72.0 if is_brute else 78.0 + (spawn_index % 4) * 9.0) * pressure,
        "damage": (22 if is_brute else 16 + (spawn_index % 3) * 2),
        "core_damage": 3 if is_brute else 2,
        "detection_range": 1250.0 + (spawn_index % 3) * 150.0,
        "attack_interval": 1.08 if is_brute else 0.92,
        "size": 1.16 if is_brute else 0.94 + (spawn_index % 3) * 0.035,
        "is_brute": is_brute,
        "heading": float((spawn_index * 73) % 360),
        "attack_cooldown": 0.0,
        "attack_animation": 0.0,
        "attack_side": -1.0 if spawn_index % 2 else 1.0,
        "aggro_timer": 0.0,
        "stun_timer": 0.0,
        "pulse": spawn_index * 1.3 + elapsed_game_time,
        "hit_flash": 0.0,
        "damaged_timer": 0.0,
    }

def begin_enemy_attack(enemy):
    enemy["attack_animation"] = ENEMY_ATTACK_ANIMATION_DURATION
    enemy["attack_side"] *= -1.0

def reset_game():
    global player_x, player_y, player_z, vertical_velocity
    global player_yaw, player_pitch, is_grounded, is_sitting
    global player_health, player_lives, player_score, elapsed_game_time
    global damage_cooldown, core_damage_cooldown, checkpoint_x, checkpoint_y
    global energy_collected, core_activated, core_upload_active
    global core_upload_progress, core_health, grid_integrity
    global missed_shots, ending_choice, game_state, bullets, enemy_projectiles
    global enemies, crystals, rift_anchors, sentries
    global particles, floating_texts, weapon_bob_phase, movement_intensity
    global weapon_sway, weapon_recoil, muzzle_flash_timer, hit_marker_timer
    global damage_flash_timer, camera_shake_timer
    global forward_velocity, turn_velocity, pitch_velocity
    global enemy_spawn_timer, enemy_spawn_cursor, navigation_field_cache
    global emp_charges, emp_cooldown, emp_effect_timer, emp_origin_x, emp_origin_y
    global sentry_charges
    build_map()
    player_x, player_y = player_start
    player_z = 0.0
    vertical_velocity = 0.0
    player_yaw = 0.0
    player_pitch = 0.0
    is_grounded = True
    is_sitting = False
    player_health = 100
    player_lives = 3
    player_score = 0
    elapsed_game_time = 0.0
    damage_cooldown = 0.0
    core_damage_cooldown = 0.0
    checkpoint_x, checkpoint_y = player_start
    energy_collected = 0
    core_activated = False
    core_upload_active = False
    core_upload_progress = 0.0
    core_health = CORE_MAX_HEALTH
    grid_integrity = GRID_MAX_INTEGRITY
    missed_shots = 0
    ending_choice = None
    game_state = "playing"
    bullets = []
    enemy_projectiles = []
    sentries = []
    particles = []
    floating_texts = []
    weapon_bob_phase = 0.0
    movement_intensity = 0.0
    weapon_sway = 0.0
    weapon_recoil = 0.0
    muzzle_flash_timer = 0.0
    hit_marker_timer = 0.0
    damage_flash_timer = 0.0
    camera_shake_timer = 0.0
    forward_velocity = 0.0
    turn_velocity = 0.0
    pitch_velocity = 0.0
    enemy_spawn_timer = 5.0
    enemy_spawn_cursor = 0
    navigation_field_cache = {}
    emp_charges = EMP_MAX_CHARGES
    emp_cooldown = 0.0
    emp_effect_timer = 0.0
    emp_origin_x, emp_origin_y = player_start
    sentry_charges = SENTRY_MAX_CHARGES
    held_keys.clear()
    held_special_keys.clear()
    key_activity_until.clear()
    special_activity_until.clear()
    crystals = []
    rift_anchors = []

    for index, (x, y) in enumerate(crystal_positions):
        crystals.append({
            "x": x, "y": y, "taken": False, "spin": 0.0,
            "anchor_index": index,
        })
        rift_anchors.append({
            "x": x, "y": y,
            "health": RIFT_ANCHOR_MAX_HEALTH,
            "max_health": RIFT_ANCHOR_MAX_HEALTH,
            "active": True,
            "spin": index * 83.0,
            "hit_flash": 0.0,
            "fire_cooldown": 2.0 + index * 0.65,
        })
    enemies = []
    initial_count = min(INITIAL_ACTIVE_ENEMIES, len(enemy_spawn_points))
    for index in range(initial_count):
        spawn_index = (index * 5 + 2) % len(enemy_spawn_points)
        enemies.append(create_enemy(spawn_index))
    enemy_spawn_cursor = (initial_count * 5 + 2) % len(enemy_spawn_points)
    set_status(
        "Follow the magenta arrow. Shoot the Anchor 5 times, then collect its bright pink memory.",
        8.0,
    )


# Drawing helpers
def draw_cube(size, color):
    glColor3f(*color)
    glutSolidCube(size)

def draw_cylinder_between(start, end, radius, color):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dz = end[2] - start[2]
    length = sqrt(dx * dx + dy * dy + dz * dz)
    if length < 0.001:
        return
    glPushMatrix()
    glTranslatef(*start)
    angle = degrees(acos(max(-1.0, min(1.0, dz / length))))
    axis_x = -dy / length
    axis_y = dx / length
    if angle > 0.01:
        glRotatef(angle, axis_x, axis_y, 0.0)
    glColor3f(*color)
    gluCylinder(quadric, radius, radius * 0.9, length, 10, 4)
    glPopMatrix()

def draw_text(x, y, message, font=GLUT_BITMAP_HELVETICA_18,
              color=(1.0, 1.0, 1.0)):
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for character in str(message):
        glutBitmapCharacter(font, ord(character))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def begin_overlay():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)

def end_overlay():
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_screen_rect(x1, y1, x2, y2, color):
    if len(color) == 4:
        glColor4f(*color)
    else:
        glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x1, y1)
    glVertex2f(x2, y1)
    glVertex2f(x2, y2)
    glVertex2f(x1, y2)
    glEnd()

def draw_screen_circle(center_x, center_y, radius, color, segments=28):
    if len(color) == 4:
        glColor4f(*color)
    else:
        glColor3f(*color)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(center_x, center_y)
    for index in range(segments + 1):
        angle = radians(index * 360.0 / segments)
        glVertex2f(center_x + cos(angle) * radius,
                   center_y + sin(angle) * radius)
    glEnd()

def draw_floor_tile(row, col, symbol):
    x1 = col * CELL - WORLD_W / 2.0
    y1 = WORLD_H / 2.0 - (row + 1) * CELL
    x2 = x1 + CELL
    y2 = y1 + CELL
    center_x = (x1 + x2) / 2.0
    center_y = (y1 + y2) / 2.0
    variation = (((row * 17 + col * 29) % 9) - 4) * 0.007

    if symbol == "h":
        base = (0.095, 0.105, 0.115)
    elif row in (5, 9, 13, 19, 22):
        base = (0.13, 0.17, 0.18)
    else:
        base = TERRAIN_BASE_COLOR if (row + col) % 3 else TERRAIN_ALT_COLOR

    corner_colors = [
        tuple(max(0.0, value + variation) for value in base),
        tuple(max(0.0, value - 0.012) for value in base),
        tuple(max(0.0, value + 0.016) for value in base),
        tuple(max(0.0, value - variation) for value in base),
    ]
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    glNormal3f(0.0, 0.0, 1.0)
    glBegin(GL_TRIANGLES)
    for index in range(4):
        next_index = (index + 1) % 4
        glColor3f(*corner_colors[index])
        glVertex3f(corners[index][0], corners[index][1], 0.0)
        glColor3f(*corner_colors[next_index])
        glVertex3f(corners[next_index][0], corners[next_index][1], 0.0)
        glColor3f(*(tuple((a + b) * 0.5 for a, b in
                          zip(corner_colors[index], corner_colors[next_index]))))
        glVertex3f(center_x, center_y, 1.5)
    glEnd()

    if (row, col) in rift_cells:
        glDisable(GL_LIGHTING)
        glLineWidth(1.8)
        glColor3f(*MAGENTA_COLOR)
        glBegin(GL_LINE_STRIP)
        glVertex3f(x1 + 20.0, y1 + 42.0, 3.0)
        glVertex3f(center_x - 22.0, center_y - 10.0, 3.5)
        glVertex3f(center_x + 15.0, center_y + 18.0, 3.5)
        glVertex3f(x2 - 24.0, y2 - 38.0, 3.0)
        glEnd()
        glEnable(GL_LIGHTING)

    if row in (5, 9, 13, 19, 22) and col % 4 == 1:
        glDisable(GL_LIGHTING)
        glColor3f(0.20, 0.65, 0.67)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex3f(x1 + 45.0, center_y, 2.5)
        glVertex3f(x2 - 45.0, center_y, 2.5)
        glEnd()
        glEnable(GL_LIGHTING)


def draw_spike_trap(row, col):
    x, y = world_from_cell(row, col)
    extension = trap_extension(row, col)
    warning = 0.5 + 0.5 * sin(elapsed_game_time * 7.0 + row + col)
    glPushMatrix()
    glTranslatef(x, y, 0.0)
    glPushMatrix()
    glTranslatef(0.0, 0.0, 6.0)
    glScalef(1.0, 1.0, 0.08)
    draw_cube(166.0, (0.13, 0.15, 0.17))
    glPopMatrix()
    for rail_x, rail_y, scale_x, scale_y in (
            (0.0, -82.0, 1.0, 0.09), (0.0, 82.0, 1.0, 0.09),
            (-82.0, 0.0, 0.09, 1.0), (82.0, 0.0, 0.09, 1.0)):
        glPushMatrix()
        glTranslatef(rail_x, rail_y, 13.0)
        glScalef(scale_x, scale_y, 0.12)
        draw_cube(168.0, (0.22, 0.25, 0.27))
        glPopMatrix()

    for spike_row in range(3):
        for spike_col in range(3):
            spike_x = (spike_col - 1) * 47.0
            spike_y = (spike_row - 1) * 47.0
            spike_height = 7.0 + extension * (53.0 + (spike_row + spike_col) % 2 * 8.0)
            glPushMatrix()
            glTranslatef(spike_x, spike_y, 9.0)
            glColor3f(0.42 + extension * 0.26,
                      0.44 + extension * 0.18,
                      0.46 + extension * 0.12)
            glutSolidCone(9.5, spike_height, 9, 4)
            glPopMatrix()

    glDisable(GL_LIGHTING)
    lamp_color = ((1.0, 0.12, 0.025) if extension > 0.58
                  else (1.0, 0.52 + warning * 0.22, 0.04))
    for lamp_x, lamp_y in ((-70, -70), (70, -70), (70, 70), (-70, 70)):
        glPushMatrix()
        glTranslatef(lamp_x, lamp_y, 19.0)
        glColor3f(*lamp_color)
        gluSphere(quadric, 5.5, 8, 5)
        glPopMatrix()
    glColor3f(*lamp_color)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    for index in range(24):
        angle = radians(index * 15.0)
        glVertex3f(cos(angle) * 32.0, sin(angle) * 32.0, 16.5)
    glEnd()
    glEnable(GL_LIGHTING)
    glPopMatrix()

def draw_sky():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window_width, 0, window_height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)
    glBegin(GL_QUADS)
    glColor3f(*SKY_HORIZON_COLOR)
    glVertex2f(0, 0)
    glVertex2f(window_width, 0)
    glColor3f(0.018, 0.045, 0.085)
    glVertex2f(window_width, window_height * 0.52)
    glVertex2f(0, window_height * 0.52)
    glColor3f(0.018, 0.045, 0.085)
    glVertex2f(0, window_height * 0.52)
    glVertex2f(window_width, window_height * 0.52)
    glColor3f(*SKY_TOP_COLOR)
    glVertex2f(window_width, window_height)
    glVertex2f(0, window_height)
    glEnd()

    draw_screen_rect(0, window_height * 0.17, window_width,
                     window_height * 0.235, (0.035, 0.125, 0.165))
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glPointSize(2.0)
    glBegin(GL_POINTS)
    for star_index in range(76):
        star_x = ((star_index * 193 + 71) % 997) / 997.0 * window_width
        star_y = window_height * (0.34 +
                                  ((star_index * 109 + 37) % 613) / 613.0 * 0.63)
        twinkle = 0.68 + 0.24 * sin(elapsed_game_time * 1.7 + star_index * 2.1)
        glColor4f(0.70 * twinkle, 0.82 * twinkle, twinkle,
                  0.58 + (star_index % 4) * 0.10)
        glVertex2f(star_x, star_y)
    glEnd()

    def draw_sky_disc(center_x, center_y, radius, color, segments=32):
        glColor4f(*color)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(center_x, center_y)
        for disc_index in range(segments + 1):
            angle = radians(disc_index * 360.0 / segments)
            glVertex2f(center_x + cos(angle) * radius,
                       center_y + sin(angle) * radius)
        glEnd()
    moon_x = window_width * 0.82
    moon_y = window_height * 0.78
    moon_radius = max(29.0, min(window_width, window_height) * 0.057)
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.62, 0.78, 1.0, 0.26)
    glVertex2f(moon_x, moon_y)
    glColor4f(0.42, 0.62, 0.90, 0.0)
    for index in range(41):
        angle = radians(index * 360.0 / 40.0)
        glVertex2f(moon_x + cos(angle) * moon_radius * 1.85,
                   moon_y + sin(angle) * moon_radius * 1.85)
    glEnd()
    draw_sky_disc(moon_x, moon_y, moon_radius, (0.80, 0.86, 0.91, 1.0), 40)
    draw_sky_disc(moon_x - moon_radius * 0.28, moon_y + moon_radius * 0.21,
                  moon_radius * 0.17, (0.48, 0.57, 0.66, 0.25), 18)
    draw_sky_disc(moon_x + moon_radius * 0.25, moon_y - moon_radius * 0.18,
                  moon_radius * 0.23, (0.45, 0.54, 0.63, 0.20), 18)
    draw_sky_disc(moon_x + moon_radius * 0.12, moon_y + moon_radius * 0.36,
                  moon_radius * 0.10, (0.46, 0.55, 0.64, 0.22), 16)
    def draw_cloud(cloud_x, cloud_y, cloud_scale, alpha):
        for offset_x, offset_y, radius in (
                (-46.0, 4.0, 30.0), (-14.0, 18.0, 37.0),
                (24.0, 15.0, 34.0), (51.0, 2.0, 27.0)):
            draw_sky_disc(
                cloud_x + offset_x * cloud_scale,
                cloud_y + offset_y * cloud_scale,
                radius * cloud_scale,
                (0.16, 0.22, 0.31, alpha),
                20,
            )

    cloud_drift = (elapsed_game_time * 2.4) % (window_width + 240.0)
    draw_cloud(cloud_drift - 120.0, window_height * 0.69, 0.78, 0.48)
    draw_cloud(window_width - cloud_drift * 0.55,
               window_height * 0.87, 0.52, 0.38)
    draw_cloud(window_width * 0.48, window_height * 0.58, 0.42, 0.30)
    glColor4f(*BIRD_COLOR, 0.92)
    glLineWidth(2.5)
    for bird_index in range(7):
        bird_x = ((elapsed_game_time * (20.0 + bird_index * 4.0)
                   + bird_index * 193.0) % (window_width + 180.0)) - 90.0
        bird_y = window_height * (0.56 + (bird_index % 4) * 0.075)
        bird_y += sin(elapsed_game_time * 1.35 + bird_index) * 13.0
        bird_size = 8.0 + (bird_index % 3) * 2.5
        wing_lift = sin(elapsed_game_time * 5.2 + bird_index) * bird_size * 0.48
        glBegin(GL_LINES)
        glVertex2f(bird_x - bird_size, bird_y + wing_lift)
        glVertex2f(bird_x, bird_y)
        glVertex2f(bird_x, bird_y)
        glVertex2f(bird_x + bird_size, bird_y + wing_lift)
        glEnd()

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def apply_face_normal(point_a, point_b, point_c):
    ux = point_b[0] - point_a[0]
    uy = point_b[1] - point_a[1]
    uz = point_b[2] - point_a[2]
    vx = point_c[0] - point_a[0]
    vy = point_c[1] - point_a[1]
    vz = point_c[2] - point_a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    length = sqrt(nx * nx + ny * ny + nz * nz)
    if length > 0.001:
        glNormal3f(nx / length, ny / length, nz / length)


def draw_low_poly_rock(scale=1.0, color=(0.21, 0.27, 0.27)):
    bottom = [(-25, -20, 0), (23, -24, 0), (31, 15, 0), (-18, 28, 0)]
    top = [(-13, -11, 28), (14, -13, 34), (19, 8, 30), (-9, 16, 38)]
    glPushMatrix()
    glScalef(scale, scale, scale)
    for index in range(4):
        next_index = (index + 1) % 4
        apply_face_normal(bottom[index], bottom[next_index], top[next_index])
        shade = 0.72 + index * 0.075
        glColor3f(color[0] * shade, color[1] * shade, color[2] * shade)
        glBegin(GL_QUADS)
        glVertex3f(*bottom[index])
        glVertex3f(*bottom[next_index])
        glVertex3f(*top[next_index])
        glVertex3f(*top[index])
        glEnd()
    apply_face_normal(top[0], top[1], top[2])
    glColor3f(min(1.0, color[0] * 1.18), min(1.0, color[1] * 1.18),
              min(1.0, color[2] * 1.18))
    glBegin(GL_QUADS)
    for point in top:
        glVertex3f(*point)
    glEnd()
    glPopMatrix()


def draw_irregular_cliff(row, col):
    half = CELL * 0.5
    base_height = 205.0 + ((row * 13 + col * 19) % 65)
    bottom = [(-half, -half, 0), (half, -half, 0),
              (half, half, 0), (-half, half, 0)]
    top = [
        (-half + 8, -half + 13, base_height + ((row + col) % 3) * 18),
        (half - 15, -half + 7, base_height + ((row * 3 + col) % 4) * 12),
        (half - 8, half - 16, base_height + ((row + col * 2) % 5) * 10),
        (-half + 18, half - 9, base_height + ((row * 2 + col) % 4) * 15),
    ]
    face_colors = [(0.13, 0.18, 0.19), (0.16, 0.22, 0.22),
                   (0.18, 0.25, 0.24), (0.12, 0.17, 0.18)]
    for index in range(4):
        next_index = (index + 1) % 4
        apply_face_normal(bottom[index], bottom[next_index], top[next_index])
        glColor3f(*face_colors[index])
        glBegin(GL_QUADS)
        glVertex3f(*bottom[index])
        glVertex3f(*bottom[next_index])
        glVertex3f(*top[next_index])
        glVertex3f(*top[index])
        glEnd()
    center = (sum(point[0] for point in top) / 4.0,
              sum(point[1] for point in top) / 4.0,
              sum(point[2] for point in top) / 4.0 + 4.0)
    glColor3f(0.22, 0.31, 0.28)
    glBegin(GL_TRIANGLES)
    for index in range(4):
        next_index = (index + 1) % 4
        apply_face_normal(top[index], top[next_index], center)
        glVertex3f(*top[index])
        glVertex3f(*top[next_index])
        glVertex3f(*center)
    glEnd()

    if (row * 7 + col * 11) % 9 == 0:
        glDisable(GL_LIGHTING)
        glColor3f(0.05, 0.62, 0.72)
        glLineWidth(2.0)
        glBegin(GL_LINE_STRIP)
        glVertex3f(-half - 0.5, -34.0, 30.0)
        glVertex3f(-half - 0.5, 3.0, 95.0)
        glVertex3f(-half - 0.5, -18.0, 150.0)
        glEnd()
        glEnable(GL_LIGHTING)


def draw_tree_shadow(radius=72.0):
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0.005, 0.008, 0.012, 0.46)
    glVertex3f(0.0, 0.0, 2.1)
    glColor4f(0.005, 0.008, 0.012, 0.0)
    for index in range(17):
        angle = radians(index * 360.0 / 16.0)
        glVertex3f(cos(angle) * radius, sin(angle) * radius * 0.46, 2.1)
    glEnd()
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)


def draw_stylized_tree(variation=0.35):
    draw_tree_shadow(78.0)
    bark = (0.16 + variation * 0.025, 0.105 + variation * 0.018, 0.075)
    glColor3f(*bark)
    gluCylinder(quadric, 20.0, 11.0, 148.0, 9, 4)
    for start, end, radius in (
            ((-2, 0, 67), (-43, 7, 119), 6.5),
            ((2, -1, 84), (39, -13, 132), 6.0),
            ((0, 2, 106), (-24, 25, 151), 5.2),
            ((0, 0, 5), (34, 13, 3), 6.0),
            ((0, 0, 5), (-29, -17, 3), 5.5)):
        draw_cylinder_between(start, end, radius, bark)

    foliage = (
        (0, 0, 151, 1.00, 0.00),
        (-35, 9, 132, 0.70, -0.025),
        (33, -8, 137, 0.75, 0.018),
        (-17, 23, 169, 0.62, 0.035),
        (24, 16, 163, 0.58, -0.012),
    )
    for x_offset, y_offset, z_offset, scale, color_shift in foliage:
        glPushMatrix()
        glTranslatef(x_offset, y_offset, z_offset)
        glScalef(0.88 * scale, 0.80 * scale, 1.10 * scale)
        glColor3f(0.055 + variation * 0.018,
                  0.205 + variation * 0.045 + color_shift,
                  0.165 + variation * 0.030)
        gluSphere(quadric, 55.0, 8, 6)
        glPopMatrix()
    glDisable(GL_LIGHTING)
    glPointSize(2.5)
    glColor3f(0.28, 0.53, 0.52)
    glBegin(GL_POINTS)
    glVertex3f(-21.0, 6.0, 177.0)
    glVertex3f(28.0, -4.0, 158.0)
    glVertex3f(3.0, 17.0, 190.0)
    glEnd()
    glEnable(GL_LIGHTING)


def draw_decoration(item):
    glPushMatrix()
    glTranslatef(item["x"], item["y"], 0.0)
    scale = item["scale"]
    if item["type"] == "tree":
        glRotatef(item["rotation"], 0.0, 0.0, 1.0)
        glScalef(scale, scale, scale)
        draw_stylized_tree(item["variation"])
    elif item["type"] == "grass":
        glDisable(GL_LIGHTING)
        glColor3f(0.13, 0.29, 0.19)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        for blade in range(7):
            blade_x = (blade - 3) * 5.0 * scale
            blade_y = ((blade * 11) % 5 - 2) * 3.0
            glVertex3f(blade_x, blade_y, 1.5)
            glVertex3f(blade_x + ((blade % 3) - 1) * 5.0,
                       blade_y + 2.0, (19.0 + blade % 3 * 5.0) * scale)
        glEnd()
        glEnable(GL_LIGHTING)
    elif item["type"] == "rock":
        draw_low_poly_rock(scale)
    elif item["type"] == "shard":
        glDisable(GL_LIGHTING)
        glColor3f(0.42, 0.06, 0.62)
        glRotatef(18.0, 1.0, 0.0, 0.0)
        glScalef(8.0 * scale, 8.0 * scale, 30.0 * scale)
        gluSphere(quadric, 1.0, 5, 4)
        glEnable(GL_LIGHTING)
    elif item["type"] == "dead_plant":
        glColor3f(0.16, 0.22, 0.18)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 34 * scale)
        glVertex3f(0, 0, 23 * scale)
        glVertex3f(-15 * scale, 5, 42 * scale)
        glVertex3f(0, 0, 19 * scale)
        glVertex3f(13 * scale, -4, 34 * scale)
        glEnd()
    elif item["type"] == "debris":
        glRotatef((item["x"] + item["y"]) % 40.0, 0, 0, 1)
        glScalef(1.25, 0.34, 0.22)
        draw_cube(28.0 * scale, (0.18, 0.24, 0.25))
    glPopMatrix()


def draw_solid_cell(row, col, symbol):
    x, y = world_from_cell(row, col)
    glPushMatrix()
    glTranslatef(x, y, 0.0)

    if symbol == "#":
        draw_irregular_cliff(row, col)
    elif symbol == "f":
        glPushMatrix()
        glTranslatef(0.0, 0.0, 78.0)
        glRotatef(-5.0 - ((row + col) % 5), 0.0, 0.0, 1.0)
        glScalef(0.92, 0.78, 0.78)
        draw_cube(CELL, (0.19, 0.24, 0.23))
        glPopMatrix()
        glPushMatrix()
        glTranslatef(18.0, -12.0, 172.0)
        glRotatef(11.0, 0.0, 1.0, 0.0)
        glScalef(0.65, 0.64, 0.34)
        draw_cube(CELL, (0.24, 0.29, 0.27))
        glPopMatrix()
        glDisable(GL_LIGHTING)
        glColor3f(0.06, 0.70, 0.78)
        glBegin(GL_QUADS)
        glVertex3f(-42, -80.5, 62)
        glVertex3f(42, -80.5, 62)
        glVertex3f(42, -80.5, 105)
        glVertex3f(-42, -80.5, 105)
        glEnd()
        glEnable(GL_LIGHTING)
    elif symbol == "r":
        for index, (ox, oy, rock_scale) in enumerate(
                ((-48, -25, 1.15), (28, -17, 0.9), (8, 43, 0.72))):
            glPushMatrix()
            glTranslatef(ox, oy, 0.0)
            glRotatef(index * 37.0, 0, 0, 1)
            draw_low_poly_rock(rock_scale, (0.20, 0.23, 0.22))
            glPopMatrix()
    else:
        draw_stylized_tree()
    glPopMatrix()


def draw_map():
    player_row = int((WORLD_H / 2.0 - player_y) // CELL)
    player_col = int((player_x + WORLD_W / 2.0) // CELL)

    for row in range(max(0, player_row - WORLD_VIEW_CELLS),
                     min(MAP_H, player_row + WORLD_VIEW_CELLS + 1)):
        for col in range(max(0, player_col - WORLD_VIEW_CELLS),
                         min(MAP_W, player_col + WORLD_VIEW_CELLS + 1)):
            symbol = grid[row][col]
            if symbol in SOLID_CELLS:
                draw_solid_cell(row, col, symbol)
            else:
                draw_floor_tile(row, col, symbol)

                if symbol == "h":
                    draw_spike_trap(row, col)

                for item in decorations_by_cell.get((row, col), []):
                    draw_decoration(item)


def draw_core():
    energy_ratio = min(1.0, energy_collected / float(ENERGY_REQUIRED))
    core_ratio = max(0.0, core_health / float(CORE_MAX_HEALTH))
    pulse = 1.0 + sin(elapsed_game_time * 3.0) * 0.08
    glPushMatrix()
    glTranslatef(core_position[0], core_position[1], 0.0)
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)
    glColor4f(0.05, 0.72 + energy_ratio * 0.25,
              1.0 - energy_ratio * 0.18, 0.16 + energy_ratio * 0.10)
    glBegin(GL_QUADS)
    glVertex3f(-18, 0, 12)
    glVertex3f(18, 0, 12)
    glVertex3f(32, 0, 720)
    glVertex3f(-32, 0, 720)
    glVertex3f(0, -18, 12)
    glVertex3f(0, 18, 12)
    glVertex3f(0, 32, 720)
    glVertex3f(0, -32, 720)
    glEnd()
    glDepthMask(GL_TRUE)
    glTranslatef(0.0, 0.0, 86.0 + sin(elapsed_game_time * 2.2) * 8.0)
    glRotatef(elapsed_game_time * 72.0, 0.0, 0.0, 1.0)
    if core_ratio < 0.35:
        glColor3f(1.0, 0.14 + core_ratio * 0.45, 0.06)
    else:
        glColor3f(0.50 + energy_ratio * 0.30, 0.84 + energy_ratio * 0.14,
                  1.0 - energy_ratio * 0.22)
    glPushMatrix()
    glScalef(pulse, pulse, pulse)
    gluSphere(quadric, 34, 12, 9)
    glPopMatrix()
    glLineWidth(2.5)
    for ring_index, axis in enumerate(((1, 0, 0), (0, 1, 0), (1, 1, 0))):
        glPushMatrix()
        glRotatef(elapsed_game_time * (45.0 + ring_index * 18.0), *axis)
        glColor3f(0.16 + ring_index * 0.12, 0.82, 1.0)
        glBegin(GL_LINE_LOOP)
        for index in range(24):
            angle = radians(index * 15.0)
            glVertex3f(cos(angle) * (52 + ring_index * 7),
                       sin(angle) * (52 + ring_index * 7), 0.0)
        glEnd()
        glPopMatrix()

    for orbit_index in range(7):
        angle = elapsed_game_time * 1.7 + orbit_index * 6.283 / 7.0
        radius = 68.0 + (orbit_index % 2) * 10.0
        glPushMatrix()
        glTranslatef(cos(angle) * radius, sin(angle) * radius,
                     sin(angle * 1.7) * 22.0)
        glColor3f(0.72, 0.98, 1.0)
        gluSphere(quadric, 4.0, 6, 4)
        glPopMatrix()

    glDisable(GL_BLEND)
    glEnable(GL_FOG)
    glEnable(GL_LIGHTING)
    glPopMatrix()

def draw_core_activation_beacon():
    if energy_collected < ENERGY_REQUIRED or core_activated:
        return
    glPushMatrix()
    glTranslatef(core_position[0], core_position[1], 0.0)
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)
    glColor4f(0.10, 1.0, 0.58, 0.20)
    glBegin(GL_QUADS)
    glVertex3f(-22, 0, 2)
    glVertex3f(22, 0, 2)
    glVertex3f(38, 0, 560)
    glVertex3f(-38, 0, 560)
    glEnd()
    glDepthMask(GL_TRUE)
    glColor3f(0.15, 1.0, 0.62)
    glLineWidth(3.0)
    for radius in (58.0, 76.0):
        glBegin(GL_LINE_LOOP)
        for index in range(28):
            angle = radians(index * 360.0 / 28.0)
            glVertex3f(cos(angle) * radius, sin(angle) * radius, 3.0)
        glEnd()
    if core_upload_active:
        glColor4f(0.10, 1.0, 0.58, 0.52)
        glLineWidth(2.5)
        glBegin(GL_LINE_LOOP)
        for index in range(72):
            angle = radians(index * 5.0)
            glVertex3f(cos(angle) * CORE_UPLOAD_RADIUS,
                       sin(angle) * CORE_UPLOAD_RADIUS, 4.0)
        glEnd()
        upload_ratio = min(1.0, core_upload_progress / CORE_UPLOAD_DURATION)
        glColor4f(0.72, 1.0, 0.88, 0.90)
        glLineWidth(6.0)
        glBegin(GL_LINE_STRIP)
        progress_points = max(2, int(72 * upload_ratio) + 1)
        for index in range(progress_points):
            angle = radians(index * 5.0)
            glVertex3f(cos(angle) * (CORE_UPLOAD_RADIUS - 8.0),
                       sin(angle) * (CORE_UPLOAD_RADIUS - 8.0), 5.0)
        glEnd()
    glDisable(GL_BLEND)
    glEnable(GL_FOG)
    glEnable(GL_LIGHTING)
    glPopMatrix()


def draw_rift_anchors():
    for anchor_index, anchor in enumerate(rift_anchors):
        if not anchor["active"]:
            glPushMatrix()
            glTranslatef(anchor["x"], anchor["y"], 0.0)
            glPushMatrix()
            glTranslatef(0.0, 0.0, 10.0)
            glScalef(1.5, 1.5, 0.22)
            draw_cube(58.0, (0.10, 0.12, 0.13))
            glPopMatrix()
            for debris_index in range(3):
                glPushMatrix()
                angle = radians(debris_index * 120.0 + anchor_index * 19.0)
                glTranslatef(cos(angle) * 45.0, sin(angle) * 45.0, 9.0)
                glRotatef(debris_index * 41.0, 0.0, 1.0, 1.0)
                glScalef(1.4, 0.32, 0.24)
                draw_cube(25.0, (0.16, 0.12, 0.17))
                glPopMatrix()
            glPopMatrix()
            continue

        glPushMatrix()
        glTranslatef(anchor["x"], anchor["y"], 0.0)
        hit_flash = anchor["hit_flash"] > 0.0
        glPushMatrix()
        glTranslatef(0.0, 0.0, 12.0)
        glScalef(1.55, 1.55, 0.24)
        draw_cube(62.0, (0.18, 0.10, 0.23))
        glPopMatrix()
        for pylon_index in range(3):
            angle = radians(anchor["spin"] * 0.18 + pylon_index * 120.0)
            pylon_x = cos(angle) * 48.0
            pylon_y = sin(angle) * 48.0
            glPushMatrix()
            glTranslatef(pylon_x, pylon_y, 22.0)
            glRotatef(-13.0, -sin(angle), cos(angle), 0.0)
            glColor3f(0.42 if hit_flash else 0.20, 0.04, 0.29)
            gluCylinder(quadric, 9.0, 5.0, 82.0, 8, 3)
            glPopMatrix()

        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        glColor4f(0.86, 0.08, 1.0, 0.16)
        glBegin(GL_QUADS)
        glVertex3f(-13, 0, 42)
        glVertex3f(13, 0, 42)
        glVertex3f(25, 0, 430)
        glVertex3f(-25, 0, 430)
        glEnd()
        glLineWidth(3.0)
        for ring_index in range(3):
            glPushMatrix()
            glTranslatef(0.0, 0.0, 72.0 + ring_index * 24.0)
            glRotatef(anchor["spin"] * (1.0 + ring_index * 0.35),
                      1.0 if ring_index == 1 else 0.0,
                      1.0 if ring_index == 2 else 0.0, 1.0)
            glColor4f(1.0 if hit_flash else 0.82, 0.18, 1.0, 0.88)
            glBegin(GL_LINE_LOOP)
            for point_index in range(28):
                angle = radians(point_index * 360.0 / 28.0)
                radius = 62.0 + ring_index * 8.0
                glVertex3f(cos(angle) * radius, sin(angle) * radius, 0.0)
            glEnd()
            glPopMatrix()

        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)
        glPushMatrix()
        glTranslatef(0.0, 0.0, 102.0)
        glColor3f(*( (1.0, 0.62, 0.70) if hit_flash else (0.72, 0.04, 0.88) ))
        gluSphere(quadric, 22.0, 10, 7)
        glPopMatrix()
        health_ratio = anchor["health"] / float(anchor["max_health"])
        glDisable(GL_LIGHTING)
        glColor3f(0.025, 0.02, 0.035)
        glBegin(GL_QUADS)
        glVertex3f(-46, 0, 148)
        glVertex3f(46, 0, 148)
        glVertex3f(46, 0, 157)
        glVertex3f(-46, 0, 157)
        glEnd()
        glColor3f(0.88, 0.10, 1.0)
        glBegin(GL_QUADS)
        glVertex3f(-43, -1, 150)
        glVertex3f(-43 + 86 * health_ratio, -1, 150)
        glVertex3f(-43 + 86 * health_ratio, -1, 155)
        glVertex3f(-43, -1, 155)
        glEnd()
        glEnable(GL_LIGHTING)
        glPopMatrix()


def draw_crystals():
    """Draw memories as unmistakable pink objectives, even while shielded."""
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for crystal in crystals:
        if crystal["taken"]:
            continue
        anchor_active = rift_anchors[crystal["anchor_index"]]["active"]
        crystal["spin"] += 1.8
        hover = sin(elapsed_game_time * 2.8 + crystal["x"] * 0.01) * 8.0
        crystal_z = (218.0 if anchor_active else 76.0) + hover
        pulse = 1.0 + sin(elapsed_game_time * 4.2
                          + crystal["anchor_index"]) * 0.10

        glPushMatrix()
        glTranslatef(crystal["x"], crystal["y"], 0.0)

        # A bright ground locator and crossed beacon make the objective visible
        # from every approach direction without textures or shader effects.
        glLineWidth(3.0)
        glColor4f(1.0, 0.12, 0.88, 0.86)
        glBegin(GL_LINE_LOOP)
        for point_index in range(36):
            angle = radians(point_index * 10.0)
            radius = 82.0 + sin(elapsed_game_time * 3.0) * 7.0
            glVertex3f(cos(angle) * radius, sin(angle) * radius, 5.0)
        glEnd()
        glDepthMask(GL_FALSE)
        glColor4f(1.0, 0.08, 0.86, 0.17 if anchor_active else 0.28)
        glBegin(GL_QUADS)
        glVertex3f(-18.0, 0.0, 7.0)
        glVertex3f(18.0, 0.0, 7.0)
        glVertex3f(30.0, 0.0, crystal_z + 72.0)
        glVertex3f(-30.0, 0.0, crystal_z + 72.0)
        glVertex3f(0.0, -18.0, 7.0)
        glVertex3f(0.0, 18.0, 7.0)
        glVertex3f(0.0, 30.0, crystal_z + 72.0)
        glVertex3f(0.0, -30.0, crystal_z + 72.0)
        glEnd()
        glDepthMask(GL_TRUE)

        # The memory itself is always vivid pink. While locked it floats above
        # the Anchor instead of being hidden inside the generator base.
        glPushMatrix()
        glTranslatef(0.0, 0.0, crystal_z)
        glRotatef(crystal["spin"], 0.0, 0.0, 1.0)
        glScalef(0.82 * pulse, 0.82 * pulse, 1.65 * pulse)
        glColor3f(1.0, 0.16 if anchor_active else 0.34, 0.92)
        gluSphere(quadric, 28.0, 7, 5)
        glPopMatrix()

        # A rotating cage communicates that the visible memory is still locked.
        if anchor_active:
            glColor4f(0.78, 0.12, 1.0, 0.92)
            glLineWidth(2.5)
            for ring_index in range(3):
                glPushMatrix()
                glTranslatef(0.0, 0.0, crystal_z + (ring_index - 1) * 48.0)
                glRotatef(crystal["spin"] * (1.0 if ring_index != 1 else -1.3),
                          0.0, 0.0, 1.0)
                glBegin(GL_LINE_LOOP)
                for point_index in range(20):
                    angle = radians(point_index * 18.0)
                    cage_radius = 54.0 - abs(ring_index - 1) * 10.0
                    glVertex3f(cos(angle) * cage_radius,
                               sin(angle) * cage_radius, 0.0)
                glEnd()
                glPopMatrix()

        distance_to_memory = sqrt((player_x - crystal["x"]) ** 2
                                  + (player_y - crystal["y"]) ** 2)
        if distance_to_memory < 720.0:
            prompt = ("MEMORY LOCKED // SHOOT THE MAGENTA ANCHOR"
                      if anchor_active else
                      "PINK MEMORY UNLOCKED // WALK INTO THE BEAM")
            glColor3f(1.0, 0.55 if anchor_active else 0.82, 0.94)
            glRasterPos3f(-105.0, 0.0, crystal_z + 92.0)
            for character in prompt:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(character))
        glPopMatrix()
    glDisable(GL_BLEND)
    glEnable(GL_FOG)
    glEnable(GL_LIGHTING)

def spawn_particle_burst(x, y, z, color, count=10, speed=150.0):
    available = max(0, MAX_PARTICLES - len(particles))
    for index in range(min(count, available)):
        angle = (index * 2.399 + elapsed_game_time * 0.7) % 6.283
        elevation = 0.25 + (index % 5) * 0.13
        horizontal = speed * (0.55 + (index % 4) * 0.12)
        life = 0.38 + (index % 4) * 0.09
        particles.append({
            "x": x, "y": y, "z": z,
            "vx": cos(angle) * horizontal,
            "vy": sin(angle) * horizontal,
            "vz": speed * elevation,
            "life": life, "max_life": life,
            "color": color,
        })

def add_floating_text(x, y, z, text, color):
    if len(floating_texts) >= MAX_FLOATING_TEXTS:
        floating_texts.pop(0)
    floating_texts.append({"x": x, "y": y, "z": z, "text": text,
                           "color": color, "life": 0.9})

def draw_particles():
    if not particles:
        return
    glDisable(GL_LIGHTING)
    glPointSize(5.0)
    glBegin(GL_POINTS)
    for particle in particles:
        alpha = max(0.0, particle["life"] / particle["max_life"])
        glColor3f(particle["color"][0] * alpha,
                  particle["color"][1] * alpha,
                  particle["color"][2] * alpha)
        glVertex3f(particle["x"], particle["y"], particle["z"])
    glEnd()
    glEnable(GL_LIGHTING)

def draw_floating_texts():
    glDisable(GL_LIGHTING)
    for item in floating_texts:
        glColor3f(*item["color"])
        glRasterPos3f(item["x"], item["y"], item["z"])
        for character in item["text"]:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(character))
    glEnable(GL_LIGHTING)

def enemy_is_targeted(enemy):
    direction_x, direction_y = forward_vector()
    delta_x = enemy["x"] - player_x
    delta_y = enemy["y"] - player_y
    distance = sqrt(delta_x * delta_x + delta_y * delta_y)
    if distance < 1.0 or distance > 1450.0:
        return False
    dot = (delta_x * direction_x + delta_y * direction_y) / distance
    return dot > 0.992

def draw_enemy_health_bar(enemy):
    health_ratio = max(0.0, enemy["health"] / float(enemy["max_health"]))
    glDisable(GL_LIGHTING)
    glColor3f(0.025, 0.025, 0.035)
    glBegin(GL_QUADS)
    glVertex3f(-39, 2, 178)
    glVertex3f(39, 2, 178)
    glVertex3f(39, 2, 187)
    glVertex3f(-39, 2, 187)
    glEnd()
    glColor3f(1.0 - health_ratio * 0.65, 0.15 + health_ratio * 0.72, 0.08)
    glBegin(GL_QUADS)
    glVertex3f(-36, 1, 180)
    glVertex3f(-36 + 72 * health_ratio, 1, 180)
    glVertex3f(-36 + 72 * health_ratio, 1, 185)
    glVertex3f(-36, 1, 185)
    glEnd()
    glEnable(GL_LIGHTING)

def draw_enemy(enemy):
    pulse = 1.0 + 0.045 * sin(enemy["pulse"])
    hover = 5.0 + sin(enemy["pulse"] * 0.72) * 5.0
    hit_color = enemy["hit_flash"] > 0.0
    if enemy["attack_animation"] > 0.0:
        attack_progress = 1.0 - min(
            1.0, enemy["attack_animation"] / ENEMY_ATTACK_ANIMATION_DURATION
        )
        attack_curve = sin(radians(attack_progress * 180.0))
    else:
        attack_curve = 0.0
    glPushMatrix()
    glTranslatef(enemy["x"], enemy["y"], hover)
    glRotatef(enemy["heading"], 0.0, 0.0, 1.0)
    glTranslatef(0.0, attack_curve * 9.0, 0.0)
    enemy_scale = pulse * enemy["size"]
    glScalef(enemy_scale, enemy_scale, enemy_scale)

    for side in (-1.0, 1.0):
        glPushMatrix()
        glTranslatef(side * 18.0, 0.0, 0.0)
        leg_color = (0.25, 0.035, 0.12) if enemy["is_brute"] else (0.18, 0.05, 0.065)
        glColor3f(*( (0.56, 0.05, 0.065) if hit_color else leg_color ))
        gluCylinder(quadric, 11.0, 8.0, 55.0, 10, 4)
        glTranslatef(0.0, 18.0, 4.0)
        glScalef(1.0, 1.7, 0.55)
        gluSphere(quadric, 14.0, 10, 8)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0.0, 0.0, 72.0)
    glScalef(0.95, 0.75, 1.25)
    body_color = (0.40, 0.025, 0.18) if enemy["is_brute"] else (0.48, 0.035, 0.075)
    glColor3f(*( (1.0, 0.72, 0.35) if hit_color else body_color ))
    gluSphere(quadric, 34, 14, 10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0.0, 0.0, 132.0)
    head_color = (0.58, 0.045, 0.22) if enemy["is_brute"] else (0.72, 0.09, 0.055)
    glColor3f(*( (1.0, 0.82, 0.50) if hit_color else head_color ))
    gluSphere(quadric, 27, 14, 10)

    for side in (-1.0, 1.0):
        glPushMatrix()
        glTranslatef(side * 12.0, 22.0, 7.0)
        glColor3f(0.01, 0.005, 0.005)
        gluSphere(quadric, 9.0, 8, 6)
        glTranslatef(0.0, 5.0, 0.0)
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.20, 0.015)
        gluSphere(quadric, 4.0, 8, 6)
        glEnable(GL_LIGHTING)
        glPopMatrix()
    glPushMatrix()
    glTranslatef(0.0, 23.0, -8.0)
    glScalef(1.4, 0.35, 0.45)
    glColor3f(0.01, 0.005, 0.005)
    glutSolidCube(24)
    glPopMatrix()
    for side in (-1.0, 1.0):
        glPushMatrix()
        glTranslatef(side * 9.0, 29.0, -13.0)
        glColor3f(0.98, 0.92, 0.70)
        glScalef(0.55, 0.55, 1.8)
        gluSphere(quadric, 7.0, 8, 6)
        glPopMatrix()
    glPopMatrix()

    for side in (-1.0, 1.0):
        is_striking_hand = side == enemy["attack_side"]
        strike_amount = attack_curve * (1.0 if is_striking_hand else 0.30)
        idle_swing = (sin(enemy["pulse"] * 0.62 + side) * 7.0
                      * (1.0 - attack_curve))
        arm_length = 45.0 + strike_amount * 24.0
        glPushMatrix()
        glTranslatef(side * 30.0, 0.0, 82.0)
        glRotatef(side * (72.0 - strike_amount * 48.0), 0.0, 1.0, 0.0)
        glRotatef(-strike_amount * 82.0 + idle_swing, 1.0, 0.0, 0.0)
        arm_color = ((0.50, 0.025, 0.17) if enemy["is_brute"]
                     else (0.42, 0.025, 0.055))
        glColor3f(*arm_color)
        gluCylinder(quadric, 9.0, 7.0, arm_length, 10, 4)
        glTranslatef(0.0, 0.0, arm_length + 3.0)
        glColor3f(0.12, 0.015, 0.02)
        gluSphere(quadric, 15.0 + strike_amount * 2.0, 10, 8)

        # Three visible claws travel with the hand during the strike.
        for claw_index in (-1, 0, 1):
            glPushMatrix()
            glTranslatef(claw_index * 6.0, 0.0, 8.0)
            glRotatef(claw_index * 17.0, 0.0, 1.0, 0.0)
            glColor3f(0.88, 0.72, 0.52)
            gluCylinder(quadric, 3.0, 0.8,
                        13.0 + strike_amount * 7.0, 7, 2)
            glPopMatrix()
        glPopMatrix()
    glDisable(GL_LIGHTING)
    glPushMatrix()
    glTranslatef(0.0, 27.0, 83.0)
    glColor3f(1.0, 0.18, 0.025)
    glScalef(1.3, 0.32, 0.75)
    glutSolidCube(18.0)
    glPopMatrix()
    glEnable(GL_LIGHTING)
    for side in (-1.0, 1.0):
        glPushMatrix()
        glTranslatef(side * 35.0, 0.0, 94.0)
        glRotatef(side * 18.0, 0.0, 1.0, 0.0)
        glScalef(1.4, 0.8, 0.55)
        draw_cube(26.0, (0.20, 0.025, 0.045))
        glPopMatrix()

    if enemy["stun_timer"] > 0.0:
        glDisable(GL_LIGHTING)
        glColor3f(0.10, 0.90, 1.0)
        glLineWidth(3.0)
        glPushMatrix()
        glTranslatef(0.0, 0.0, 172.0)
        glRotatef(elapsed_game_time * 210.0, 0.0, 0.0, 1.0)
        glBegin(GL_LINE_LOOP)
        for index in range(24):
            angle = radians(index * 15.0)
            glVertex3f(cos(angle) * 31.0, sin(angle) * 31.0, 0.0)
        glEnd()
        glPopMatrix()
        glEnable(GL_LIGHTING)

    if enemy["damaged_timer"] > 0.0 or enemy_is_targeted(enemy):
        draw_enemy_health_bar(enemy)
    glPopMatrix()


def draw_first_person_hands():
    eye_height = SITTING_EYE_HEIGHT if is_sitting else STANDING_EYE_HEIGHT
    direction_x, direction_y = forward_vector()
    right_x, right_y = direction_y, -direction_x
    bob_x = sin(weapon_bob_phase) * 3.5 * movement_intensity
    bob_z = abs(cos(weapon_bob_phase)) * 3.0 * movement_intensity
    sway_x = max(-8.0, min(8.0, weapon_sway * 0.10))
    hand_z = player_z + eye_height - (68.0 if is_sitting else 61.0) + bob_z
    shoulder_z = player_z + eye_height - 28.0

    for side in (-1.0, 1.0):
        shoulder = (
            player_x + direction_x * 39.0 + right_x * side * 13.0,
            player_y + direction_y * 39.0 + right_y * side * 13.0,
            shoulder_z,
        )
        hand = (
            player_x + direction_x * (96.0 - weapon_recoil * 8.0)
            + right_x * (side * 19.0 + bob_x + sway_x),
            player_y + direction_y * (96.0 - weapon_recoil * 8.0)
            + right_y * (side * 19.0 + bob_x + sway_x),
            hand_z,
        )
        draw_cylinder_between(shoulder, hand, 6.5, (0.24, 0.30, 0.31))
        glPushMatrix()
        glTranslatef(*hand)
        glColor3f(0.30, 0.40, 0.42)
        gluSphere(quadric, 9.5, 8, 6)
        glPopMatrix()

    weapon = (
        player_x + direction_x * (WEAPON_FORWARD_OFFSET - weapon_recoil * 16.0)
        + right_x * (bob_x + sway_x),
        player_y + direction_y * (WEAPON_FORWARD_OFFSET - weapon_recoil * 16.0)
        + right_y * (bob_x + sway_x),
        player_z + eye_height - WEAPON_VERTICAL_OFFSET + bob_z,
    )
    glPushMatrix()
    glTranslatef(*weapon)
    glRotatef(player_yaw, 0.0, 0.0, 1.0)
    glScalef(0.42, 1.35, 0.42)
    draw_cube(24.0, (0.10, 0.15, 0.18))
    glPopMatrix()

    muzzle = (
        player_x + direction_x * (145.0 - weapon_recoil * 12.0)
        + right_x * (bob_x + sway_x),
        player_y + direction_y * (145.0 - weapon_recoil * 12.0)
        + right_y * (bob_x + sway_x),
        weapon[2] + 2.0,
    )
    draw_cylinder_between(weapon, muzzle, 5.0, (0.16, 0.23, 0.27))
    glDisable(GL_LIGHTING)
    glPushMatrix()
    glTranslatef(weapon[0] + right_x * 5.5, weapon[1] + right_y * 5.5,
                 weapon[2] + 4.0)
    glColor3f(*CYAN_COLOR)
    gluSphere(quadric, 3.5, 6, 4)
    glPopMatrix()
    if muzzle_flash_timer > 0.0:
        flash_scale = muzzle_flash_timer / 0.10
        glPushMatrix()
        glTranslatef(*muzzle)
        glColor3f(0.72, 1.0, 1.0)
        gluSphere(quadric, 12.0 * flash_scale + 3.0, 8, 6)
        glPopMatrix()
    glEnable(GL_LIGHTING)


def draw_bullets():
    glDisable(GL_LIGHTING)
    for bullet in bullets:
        glLineWidth(3.0)
        glColor3f(0.08, 0.82, 1.0)
        glBegin(GL_LINES)
        glVertex3f(bullet["prev_x"], bullet["prev_y"], bullet["prev_z"])
        glVertex3f(bullet["x"], bullet["y"], bullet["z"])
        glEnd()
        glPushMatrix()
        glTranslatef(bullet["x"], bullet["y"], bullet["z"])
        glColor3f(0.72, 1.0, 1.0)
        gluSphere(quadric, 5.0, 7, 5)
        glPopMatrix()
    glEnable(GL_LIGHTING)


def draw_enemy_projectiles():
    glDisable(GL_LIGHTING)
    for projectile in enemy_projectiles:
        glLineWidth(4.0)
        glColor3f(0.95, 0.08, 0.72)
        glBegin(GL_LINES)
        glVertex3f(projectile["prev_x"], projectile["prev_y"], projectile["prev_z"])
        glVertex3f(projectile["x"], projectile["y"], projectile["z"])
        glEnd()
        glPushMatrix()
        glTranslatef(projectile["x"], projectile["y"], projectile["z"])
        glColor3f(1.0, 0.22, 0.66)
        gluSphere(quadric, 8.0, 8, 6)
        glPopMatrix()
    glEnable(GL_LIGHTING)


def draw_sentries():
    for sentry in sentries:
        glPushMatrix()
        glTranslatef(sentry["x"], sentry["y"], 0.0)
        draw_cylinder_between((-25, -18, 3), (0, 0, 36), 4.5,
                              (0.18, 0.26, 0.28))
        draw_cylinder_between((25, -18, 3), (0, 0, 36), 4.5,
                              (0.18, 0.26, 0.28))
        draw_cylinder_between((0, 28, 3), (0, 0, 36), 4.5,
                              (0.18, 0.26, 0.28))
        glPushMatrix()
        glTranslatef(0.0, 0.0, 42.0)
        glColor3f(0.14, 0.24, 0.27)
        gluSphere(quadric, 20.0, 10, 7)
        glRotatef(sentry["heading"], 0.0, 0.0, 1.0)
        glRotatef(-90.0, 1.0, 0.0, 0.0)
        glColor3f(0.22, 0.38, 0.42)
        gluCylinder(quadric, 7.0, 5.0, 45.0, 9, 3)
        glPopMatrix()
        glDisable(GL_LIGHTING)
        glColor3f(0.12, 0.95, 1.0)
        glBegin(GL_LINE_LOOP)
        life_ratio = max(0.0, sentry["life"] / SENTRY_LIFETIME)
        for index in range(24):
            angle = radians(index * 360.0 / 24.0)
            radius = 28.0 + life_ratio * 4.0
            glVertex3f(cos(angle) * radius, sin(angle) * radius, 4.0)
        glEnd()
        glEnable(GL_LIGHTING)
        glPopMatrix()

        if sentry["beam_timer"] > 0.0:
            glDisable(GL_LIGHTING)
            glLineWidth(3.0)
            glColor3f(0.12, 0.95, 1.0)
            glBegin(GL_LINES)
            glVertex3f(sentry["x"], sentry["y"], 46.0)
            glVertex3f(sentry["beam_x"], sentry["beam_y"], sentry["beam_z"])
            glEnd()
            glEnable(GL_LIGHTING)


def draw_emp_effect():
    if emp_effect_timer <= 0.0:
        return
    progress = 1.0 - min(1.0, emp_effect_timer / 0.72)
    glDisable(GL_LIGHTING)
    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for ring_offset in (0.0, 0.13, 0.26):
        ring_progress = max(0.0, min(1.0, progress - ring_offset))
        radius = EMP_RADIUS * ring_progress
        alpha = max(0.0, 0.78 - ring_progress * 0.72)
        glColor4f(0.08, 0.86, 1.0, alpha)
        glLineWidth(4.0 - ring_offset * 5.0)
        glBegin(GL_LINE_LOOP)
        for index in range(48):
            angle = radians(index * 360.0 / 48.0)
            glVertex3f(emp_origin_x + cos(angle) * radius,
                       emp_origin_y + sin(angle) * radius, 18.0)
        glEnd()
    glDisable(GL_BLEND)
    glEnable(GL_FOG)
    glEnable(GL_LIGHTING)


def draw_crosshair():
    center_x = window_width / 2.0
    center_y = window_height / 2.0
    begin_overlay()
    for width, color, extension in (
            (4.0, (0.01, 0.03, 0.05), 1.5),
            (1.8, CYAN_COLOR, 0.0)):
        glLineWidth(width)
        glColor3f(*color)
        glBegin(GL_LINES)
        glVertex2f(center_x - 18 - extension, center_y)
        glVertex2f(center_x - 6, center_y)
        glVertex2f(center_x + 6, center_y)
        glVertex2f(center_x + 18 + extension, center_y)
        glVertex2f(center_x, center_y - 18 - extension)
        glVertex2f(center_x, center_y - 6)
        glVertex2f(center_x, center_y + 6)
        glVertex2f(center_x, center_y + 18 + extension)
        glEnd()

    if hit_marker_timer > 0.0:
        glColor3f(1.0, 0.25, 0.08)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        for x_sign, y_sign in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            glVertex2f(center_x + x_sign * 7, center_y + y_sign * 7)
            glVertex2f(center_x + x_sign * 14, center_y + y_sign * 14)
        glEnd()
    end_overlay()


def current_objective_crystal():
    """Return the nearest unfinished memory objective, if one remains."""
    available = [crystal for crystal in crystals if not crystal["taken"]]
    if energy_collected < ENERGY_REQUIRED and available:
        return min(
            available,
            key=lambda crystal: ((crystal["x"] - player_x) ** 2
                                 + (crystal["y"] - player_y) ** 2),
        )
    return None


def current_objective_target():
    objective_crystal = current_objective_crystal()
    if objective_crystal is not None:
        return objective_crystal["x"], objective_crystal["y"]
    return core_position


def draw_hud():
    panel_margin = max(12.0, window_width * 0.012)
    panel_width = min(440.0, window_width * 0.46)
    panel_top = window_height - panel_margin
    panel_bottom = panel_top - 165.0
    health_ratio = max(0.0, min(1.0, player_health / 100.0))
    destroyed_anchors = anchors_destroyed_count()
    objective_crystal = current_objective_crystal()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    begin_overlay()
    draw_screen_rect(panel_margin, panel_bottom,
                     panel_margin + panel_width, panel_top,
                     (0.015, 0.035, 0.055, 0.82))
    draw_screen_rect(panel_margin + 12, panel_bottom + 18,
                     panel_margin + panel_width - 12, panel_bottom + 34,
                     (0.03, 0.08, 0.10, 0.95))
    health_color = (0.10, 0.90, 0.78) if health_ratio > 0.35 else (1.0, 0.22, 0.06)
    draw_screen_rect(panel_margin + 14, panel_bottom + 20,
                     panel_margin + 14 + (panel_width - 28) * health_ratio,
                     panel_bottom + 32, (*health_color, 0.95))

    target_x, target_y = current_objective_target()
    delta_x = target_x - player_x
    delta_y = target_y - player_y
    objective_distance = sqrt(delta_x * delta_x + delta_y * delta_y)
    target_angle = degrees(atan2(delta_x, delta_y))
    angle_difference = (target_angle - player_yaw + 180.0) % 360.0 - 180.0
    marker_x = window_width / 2.0 + max(-window_width * 0.30,
                                       min(window_width * 0.30,
                                           angle_difference / 70.0 * window_width * 0.30))
    marker_y = window_height - 68.0
    if energy_collected >= ENERGY_REQUIRED:
        marker_color = (0.15, 1.0, 0.72)
    elif (objective_crystal is not None
          and rift_anchors[objective_crystal["anchor_index"]]["active"]):
        marker_color = MAGENTA_COLOR
    else:
        marker_color = (1.0, 0.34, 0.88)
    glColor3f(*marker_color)
    glBegin(GL_TRIANGLES)
    glVertex2f(marker_x, marker_y + 11)
    glVertex2f(marker_x - 9, marker_y - 7)
    glVertex2f(marker_x + 9, marker_y - 7)
    glEnd()

    if damage_flash_timer > 0.0:
        alpha = min(0.52, damage_flash_timer * 0.7)
        thickness = max(28.0, min(window_width, window_height) * 0.055)
        draw_screen_rect(0, 0, thickness, window_height, (0.9, 0.0, 0.02, alpha))
        draw_screen_rect(window_width - thickness, 0, window_width, window_height,
                         (0.9, 0.0, 0.02, alpha))
        draw_screen_rect(0, 0, window_width, thickness, (0.9, 0.0, 0.02, alpha))
        draw_screen_rect(0, window_height - thickness, window_width, window_height,
                         (0.9, 0.0, 0.02, alpha))

    if core_upload_active and not core_activated:
        upload_ratio = min(1.0, core_upload_progress / CORE_UPLOAD_DURATION)
        upload_width = min(300.0, window_width * 0.32)
        upload_right = window_width - panel_margin
        upload_left = upload_right - upload_width
        draw_screen_rect(upload_left, panel_top - 94,
                         upload_right, panel_top - 78,
                         (0.02, 0.08, 0.09, 0.94))
        draw_screen_rect(upload_left + 2, panel_top - 92,
                         upload_left + 2 + (upload_width - 4) * upload_ratio,
                         panel_top - 80, (0.10, 1.0, 0.60, 0.96))

    show_controls = elapsed_game_time < 8.0 or game_state == "paused"
    if show_controls:
        controls_width = min(820.0, window_width - 24.0)
        draw_screen_rect((window_width - controls_width) / 2.0, 10,
                         (window_width + controls_width) / 2.0, 44,
                         (0.015, 0.035, 0.055, 0.78))

    if game_state in ("paused", "ending_choice", "game_over", "won"):
        modal_width = min(560.0, window_width * 0.78)
        modal_height = 190.0 if game_state == "ending_choice" else 155.0
        draw_screen_rect((window_width - modal_width) / 2.0,
                         (window_height - modal_height) / 2.0,
                         (window_width + modal_width) / 2.0,
                         (window_height + modal_height) / 2.0,
                         (0.008, 0.018, 0.035, 0.90))
    end_overlay()
    glDisable(GL_BLEND)
    draw_text(panel_margin + 14, panel_top - 28,
              "NEON RIFT // LAST GUARDIAN",
              color=(0.25, 0.94, 1.0))
    draw_text(panel_margin + 14, panel_top - 57,
              f"HP {player_health:03d}     LIVES {player_lives}     SCORE {player_score}",
              font=GLUT_BITMAP_HELVETICA_12, color=(0.88, 0.96, 1.0))
    draw_text(panel_margin + 14, panel_top - 82,
              f"CORE {core_health:03d}%   GRID {grid_integrity:03d}%   MISSED {missed_shots}",
              font=GLUT_BITMAP_HELVETICA_12,
              color=(0.76, 0.90, 0.94) if core_health > 35 else (1.0, 0.30, 0.12))
    emp_display = (f"{emp_charges} READY" if emp_cooldown <= 0.0
                   else f"{emp_charges} ({emp_cooldown:.1f}s)")
    draw_text(panel_margin + 14, panel_top - 107,
              f"EMP[Q] {emp_display}   SENTRY[E] {sentry_charges}   HOSTILES {len(enemies)}",
              font=GLUT_BITMAP_HELVETICA_12, color=(0.42, 0.88, 1.0))


    if core_activated:
        core_label = "CORE ACTIVATED"
        core_color = (0.15, 1.0, 0.68)
    elif core_upload_active:
        upload_percent = int(
            min(100.0, core_upload_progress / CORE_UPLOAD_DURATION * 100.0)
        )
        core_label = f"FINAL CORE LINK {upload_percent:02d}% // HOLD POSITION"
        core_color = (0.15, 1.0, 0.68)
    elif energy_collected >= ENERGY_REQUIRED:
        core_label = "ENERGY READY // START CORE LINK"
        core_color = (0.15, 1.0, 0.68)
    else:
        core_label = (f"ANCHORS {destroyed_anchors}/{len(rift_anchors)}"
                      f" // MEMORIES {energy_collected}/{ENERGY_REQUIRED}")
        core_color = (MAGENTA_COLOR if destroyed_anchors < len(rift_anchors)
                      else (1.0, 0.58, 0.12))
    draw_text(window_width - min(330.0, window_width * 0.35) - panel_margin,
              panel_top - 28, core_label, color=core_color)
    timer_value = int(elapsed_game_time)
    timer_color = ((0.60, 0.90, 1.0) if timer_value < 60 else
                   (1.0, 0.52, 0.08) if timer_value < 120 else
                   (1.0, 0.12, 0.04))
    draw_text(marker_x - 48, marker_y - 28,
              f"{int(objective_distance)}m", GLUT_BITMAP_HELVETICA_12, marker_color)
    draw_text(window_width - 150.0 - panel_margin, panel_top - 57,
              f"TIME {timer_value:03d}s", GLUT_BITMAP_HELVETICA_18, timer_color)

    if objective_crystal is not None:
        target_anchor = rift_anchors[objective_crystal["anchor_index"]]
        if target_anchor["active"]:
            objective_instruction = (
                f"TARGET: SHOOT MAGENTA ANCHOR // HP {target_anchor['health']}/"
                f"{target_anchor['max_health']}"
            )
            instruction_color = (1.0, 0.35, 0.92)
        else:
            objective_instruction = "TARGET: COLLECT THE BRIGHT PINK MEMORY"
            instruction_color = (1.0, 0.58, 0.92)
    elif core_upload_active:
        objective_instruction = "TARGET: STAY INSIDE THE GREEN CORE-LINK RING"
        instruction_color = (0.25, 1.0, 0.68)
    else:
        objective_instruction = "TARGET: RETURN TO THE GLOWING GRID CORE"
        instruction_color = (0.25, 1.0, 0.68)
    draw_text(window_width - min(430.0, window_width * 0.44) - panel_margin,
              panel_top - 110, objective_instruction,
              GLUT_BITMAP_HELVETICA_12, instruction_color)

    if show_controls:
        draw_text(max(18.0, window_width / 2.0 - 385.0), 23,
                  "W/S MOVE  A/D AIM  SPACE JUMP  CTRL/C CROUCH  CLICK FIRE  Q EMP  E SENTRY  P PAUSE",
                  GLUT_BITMAP_HELVETICA_12, (0.68, 0.82, 0.86))

    if status_message_timer > 0.0:
        draw_text(panel_margin + 14, panel_bottom - 24, status_message,
                  GLUT_BITMAP_HELVETICA_12, (1.0, 0.70, 0.22))

    if game_state == "paused":
        draw_text(window_width / 2.0 - 48, window_height / 2.0 + 28,
                  "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24, (0.25, 0.94, 1.0))
        draw_text(window_width / 2.0 - 86, window_height / 2.0 - 8,
                  "Press P to continue", color=(0.90, 0.96, 1.0))
    elif game_state == "ending_choice":
        draw_text(window_width / 2.0 - 78, window_height / 2.0 + 54,
                  "ECHO'S HIDDEN TRUTH", GLUT_BITMAP_TIMES_ROMAN_24,
                  (0.25, 0.94, 1.0))
        draw_text(window_width / 2.0 - 218, window_height / 2.0 + 12,
                  "1  DESTROY ECHO // restore the cities, lose the memories",
                  GLUT_BITMAP_HELVETICA_12, (1.0, 0.52, 0.14))
        draw_text(window_width / 2.0 - 218, window_height / 2.0 - 24,
                  "2  MERGE WITH ECHO // preserve humanity's digital past",
                  GLUT_BITMAP_HELVETICA_12, (0.20, 1.0, 0.72))
    elif game_state == "game_over":
        draw_text(window_width / 2.0 - 68, window_height / 2.0 + 28,
                  "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24, (1.0, 0.20, 0.08))
        draw_text(window_width / 2.0 - 78, window_height / 2.0 - 8,
                  "Press R to restart", color=(1.0, 0.72, 0.22))
    elif game_state == "won":
        ending_title = "CITIES RESTORED" if ending_choice == "destroy" else "MEMORIES PRESERVED"
        ending_color = ((1.0, 0.58, 0.16) if ending_choice == "destroy"
                        else (0.20, 1.0, 0.70))
        draw_text(window_width / 2.0 - 105, window_height / 2.0 + 28,
                  ending_title, GLUT_BITMAP_TIMES_ROMAN_24, ending_color)
        draw_text(window_width / 2.0 - 94, window_height / 2.0 - 8,
                  "Press R to play again", color=(0.90, 1.0, 0.95))



def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(76.0, window_width / float(max(1, window_height)), 1.0, 5200.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    eye_height = SITTING_EYE_HEIGHT if is_sitting else STANDING_EYE_HEIGHT
    shake_strength = max(0.0, camera_shake_timer) * 7.0
    eye_x = player_x + sin(elapsed_game_time * 71.0) * shake_strength
    eye_y = player_y + cos(elapsed_game_time * 83.0) * shake_strength
    eye_z = player_z + eye_height + sin(elapsed_game_time * 97.0) * shake_strength * 0.45

    direction_x = sin(radians(player_yaw)) * cos(radians(player_pitch))
    direction_y = cos(radians(player_yaw)) * cos(radians(player_pitch))
    direction_z = sin(radians(player_pitch))

    gluLookAt(eye_x, eye_y, eye_z,
              eye_x + direction_x * 300.0,
              eye_y + direction_y * 300.0,
              eye_z + direction_z * 300.0,
              0.0, 0.0, 1.0)

def enable_world_rendering():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.20, 0.23, 0.30, 1.0))
    glLightfv(GL_LIGHT0, GL_POSITION, (0.42, -0.30, 0.86, 0.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.54, 0.65, 0.82, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.34, 0.45, 0.62, 1.0))
    glLightfv(GL_LIGHT1, GL_POSITION, (-0.62, 0.48, 0.22, 0.0))
    glLightfv(GL_LIGHT1, GL_DIFFUSE, (0.08, 0.20, 0.20, 1.0))
    glLightfv(GL_LIGHT1, GL_SPECULAR, (0.04, 0.16, 0.18, 1.0))
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogfv(GL_FOG_COLOR, FOG_COLOR)
    glFogf(GL_FOG_START, FOG_START)
    glFogf(GL_FOG_END, FOG_END)


def reshape(width, height):
    global window_width, window_height
    window_width = max(320, int(width))
    window_height = max(240, int(height))
    glViewport(0, 0, window_width, window_height)
    glutPostRedisplay()


def try_move(delta_x, delta_y):
    global player_x, player_y
    # Split movement into small collision steps. This prevents snagging and
    # tunnelling when a frame is slower than usual, while retaining wall slide.
    distance = sqrt(delta_x * delta_x + delta_y * delta_y)
    steps = max(1, int(distance / 10.0) + 1)
    step_x = delta_x / steps
    step_y = delta_y / steps
    for _ in range(steps):
        next_x = player_x + step_x
        next_y = player_y + step_y
        if not is_blocked(next_x, player_y):
            player_x = next_x
        if not is_blocked(player_x, next_y):
            player_y = next_y


def forward_vector():
    angle = radians(player_yaw)
    return sin(angle), cos(angle)


def fire_bullet():
    global weapon_recoil, muzzle_flash_timer
    direction_x, direction_y = forward_vector()
    bullet_z = player_z + (SITTING_EYE_HEIGHT if is_sitting else STANDING_EYE_HEIGHT) - 18.0
    bullet_x = player_x + direction_x * 58.0
    bullet_y = player_y + direction_y * 58.0
    bullets.append({
        "x": bullet_x,
        "y": bullet_y,
        "z": bullet_z,
        "prev_x": bullet_x,
        "prev_y": bullet_y,
        "prev_z": bullet_z,
        "dx": direction_x,
        "dy": direction_y,
        "life": 2.8,
    })
    weapon_recoil = 1.0
    muzzle_flash_timer = 0.10


def activate_emp():
    """Use one EMP charge to stun nearby enemies and erase hostile rounds."""
    global emp_charges, emp_cooldown, emp_effect_timer
    global emp_origin_x, emp_origin_y, enemy_projectiles
    if emp_charges <= 0:
        set_status("EMP instrument depleted.", 1.5)
        return
    if emp_cooldown > 0.0:
        set_status(f"EMP recharging: {emp_cooldown:.1f}s", 1.2)
        return

    emp_charges -= 1
    emp_cooldown = EMP_COOLDOWN
    emp_effect_timer = 0.72
    emp_origin_x, emp_origin_y = player_x, player_y
    stunned = 0
    for enemy in enemies:
        distance_squared = ((enemy["x"] - player_x) ** 2
                            + (enemy["y"] - player_y) ** 2)
        if distance_squared <= EMP_RADIUS ** 2:
            enemy["stun_timer"] = max(enemy["stun_timer"], EMP_STUN_DURATION)
            enemy["attack_animation"] = 0.0
            stunned += 1

    enemy_projectiles = [
        projectile for projectile in enemy_projectiles
        if ((projectile["x"] - player_x) ** 2
            + (projectile["y"] - player_y) ** 2) > EMP_RADIUS ** 2
    ]
    spawn_particle_burst(player_x, player_y, 65.0, CYAN_COLOR, 24, 210.0)
    set_status(f"EMP discharged: {stunned} Rift Beast(s) stunned.", 2.0)


def deploy_sentry():
    global sentry_charges
    if sentry_charges <= 0:
        set_status("No sentry instruments remaining.", 1.5)
        return

    direction_x, direction_y = forward_vector()
    deploy_x = player_x + direction_x * 72.0
    deploy_y = player_y + direction_y * 72.0
    if is_blocked(deploy_x, deploy_y):
        deploy_x, deploy_y = player_x, player_y
    sentries.append({
        "x": deploy_x,
        "y": deploy_y,
        "life": SENTRY_LIFETIME,
        "cooldown": 0.35,
        "heading": player_yaw % 360.0,
        "beam_timer": 0.0,
        "beam_x": deploy_x,
        "beam_y": deploy_y,
        "beam_z": 60.0,
    })
    sentry_charges -= 1
    set_status("Guardian sentry deployed. It will defend this sector for 48s.", 2.4)


def keyboard_listener(key, mouse_x, mouse_y):
    global is_sitting, game_state, ending_choice, player_score
    key = key.lower()

    current_time = time.perf_counter()
    was_held = (key in held_keys
                and (key_up_callbacks_enabled
                     or key_activity_until.get(key, 0.0) > current_time))
    held_keys.add(key)
    key_activity_until[key] = current_time + KEY_FALLBACK_TIMEOUT

    if key == b'\x1b':
        raise SystemExit
    if key == b'r' and game_state in ("game_over", "won"):
        reset_game()
        return
    if game_state == "ending_choice":
        if key == b'1':
            ending_choice = "destroy"
            player_score += 500
            game_state = "won"
            set_status("ECHO destroyed. The cities awaken as the memories fade.", 8.0)
        elif key == b'2':
            ending_choice = "merge"
            player_score += 500
            game_state = "won"
            set_status("Aegis-7 merged with ECHO. Every memory survives.", 8.0)
        return
    if key == b'p':
        if not was_held:
            if game_state == "playing":
                game_state = "paused"
            elif game_state == "paused":
                game_state = "playing"
        return
    if game_state != "playing":
        return

    if key == b'q':
        if not was_held:
            activate_emp()
        return
    if key == b'e':
        if not was_held:
            deploy_sentry()
        return

    if key in (b'c', b'\x11', b'\x12', b'\x13', b'\x01', b'\x04', b'\x17'):
        if was_held:
            return
        is_sitting = not is_sitting
        set_status("Sitting/crouching enabled." if is_sitting else "Standing.", 1.2)
        return
    if key == b' ':
        if not was_held and is_grounded and not is_sitting:
            start_jump()
        return


def keyboard_up_listener(key, mouse_x, mouse_y):
    key = key.lower()
    held_keys.discard(key)
    key_activity_until.pop(key, None)


def start_jump():
    global vertical_velocity, is_grounded
    vertical_velocity = JUMP_SPEED
    is_grounded = False


def update_player_navigation(dt):
    global player_yaw, player_pitch, weapon_bob_phase
    global movement_intensity, weapon_sway
    global forward_velocity, turn_velocity, pitch_velocity
    if game_state != "playing":
        return

    current_time = time.perf_counter()
    key_is_active = lambda value: (
        value in held_keys
        and (key_up_callbacks_enabled
             or key_activity_until.get(value, 0.0) > current_time)
    )
    special_is_active = lambda value: (
        value in held_special_keys
        and (key_up_callbacks_enabled
             or special_activity_until.get(value, 0.0) > current_time)
    )
    direction_x, direction_y = forward_vector()
    move_axis = 0.0
    if key_is_active(b'w'):
        move_axis += 1.0
    if key_is_active(b's'):
        move_axis -= 1.0

    movement_speed = SITTING_SPEED if is_sitting else WALK_SPEED
    target_velocity = movement_speed * move_axis
    move_blend = min(1.0, dt * MOVE_RESPONSE)
    forward_velocity += (target_velocity - forward_velocity) * move_blend
    if abs(forward_velocity) < 0.35 and not move_axis:
        forward_velocity = 0.0

    if abs(forward_velocity) > 0.0:
        try_move(direction_x * forward_velocity * dt,
                 direction_y * forward_velocity * dt)
        weapon_bob_phase += dt * (7.0 if is_sitting else 10.0)

    target_movement = min(1.0, abs(forward_velocity) / max(1.0, movement_speed))
    movement_intensity += (target_movement - movement_intensity) * min(1.0, dt * 9.0)

    turn_axis = 0.0
    if key_is_active(b'a') or special_is_active(GLUT_KEY_LEFT):
        turn_axis -= 1.0
    if key_is_active(b'd') or special_is_active(GLUT_KEY_RIGHT):
        turn_axis += 1.0
    target_turn_velocity = turn_axis * 155.0
    turn_velocity += (target_turn_velocity - turn_velocity) * min(1.0, dt * TURN_RESPONSE)
    if abs(turn_velocity) < 0.25 and not turn_axis:
        turn_velocity = 0.0
    player_yaw += turn_velocity * dt
    weapon_sway += ((turn_velocity / 155.0) * 34.0 - weapon_sway) * min(1.0, dt * 9.0)

    pitch_axis = 0.0
    if special_is_active(GLUT_KEY_UP):
        pitch_axis += 1.0
    if special_is_active(GLUT_KEY_DOWN):
        pitch_axis -= 1.0
    target_pitch_velocity = pitch_axis * 120.0
    pitch_velocity += ((target_pitch_velocity - pitch_velocity)
                       * min(1.0, dt * TURN_RESPONSE))
    if abs(pitch_velocity) < 0.25 and not pitch_axis:
        pitch_velocity = 0.0
    player_pitch = max(-30.0, min(35.0, player_pitch + pitch_velocity * dt))


def special_key_listener(key, mouse_x, mouse_y):
    held_special_keys.add(key)
    special_activity_until[key] = time.perf_counter() + KEY_FALLBACK_TIMEOUT


def special_key_up_listener(key, mouse_x, mouse_y):
    held_special_keys.discard(key)
    special_activity_until.pop(key, None)


def mouse_listener(button, state, mouse_x, mouse_y):
    if state == GLUT_DOWN and button == GLUT_LEFT_BUTTON and game_state == "playing":
        fire_bullet()


# Gameplay updates
def update_vertical_motion(dt):
    global player_z, vertical_velocity, is_grounded
    if is_grounded:
        return
    player_z += vertical_velocity * dt
    vertical_velocity -= GRAVITY * dt
    if player_z <= 0.0:
        player_z = 0.0
        vertical_velocity = 0.0
        is_grounded = True

def update_rift_anchors(dt):
    stage = anchors_destroyed_count()
    for anchor_index, anchor in enumerate(rift_anchors):
        anchor["hit_flash"] = max(0.0, anchor["hit_flash"] - dt)
        anchor["spin"] = (anchor["spin"] + dt * (72.0 + stage * 9.0)) % 360.0
        if not anchor["active"]:
            continue
        anchor["fire_cooldown"] -= dt
        delta_x = player_x - anchor["x"]
        delta_y = player_y - anchor["y"]
        player_distance = sqrt(delta_x * delta_x + delta_y * delta_y)
        if anchor["fire_cooldown"] > 0.0 or player_distance > 1550.0:
            continue

        start_x, start_y, start_z = anchor["x"], anchor["y"], 108.0
        target_z = player_z + (SITTING_EYE_HEIGHT if is_sitting
                               else STANDING_EYE_HEIGHT) * 0.72
        aim_x = player_x - start_x
        aim_y = player_y - start_y
        aim_z = target_z - start_z
        aim_length = sqrt(aim_x * aim_x + aim_y * aim_y + aim_z * aim_z)
        if aim_length > 0.001:
            projectile_speed = 385.0 + stage * 26.0
            enemy_projectiles.append({
                "x": start_x, "y": start_y, "z": start_z,
                "prev_x": start_x, "prev_y": start_y, "prev_z": start_z,
                "vx": aim_x / aim_length * projectile_speed,
                "vy": aim_y / aim_length * projectile_speed,
                "vz": aim_z / aim_length * projectile_speed,
                "life": 5.0,
            })
        anchor["fire_cooldown"] = max(
            1.85,
            3.8 - stage * 0.32 - elapsed_game_time * 0.004
            + anchor_index * 0.18,
        )

def update_enemy_projectiles(dt):
    global enemy_projectiles, player_health, damage_cooldown
    global damage_flash_timer, camera_shake_timer
    remaining = []
    eye_z = player_z + (SITTING_EYE_HEIGHT if is_sitting else STANDING_EYE_HEIGHT)
    for projectile in enemy_projectiles:
        projectile["prev_x"] = projectile["x"]
        projectile["prev_y"] = projectile["y"]
        projectile["prev_z"] = projectile["z"]
        projectile["x"] += projectile["vx"] * dt
        projectile["y"] += projectile["vy"] * dt
        projectile["z"] += projectile["vz"] * dt
        projectile["life"] -= dt
        if projectile["life"] <= 0.0 or projectile["z"] < 3.0:
            continue
        if (cell_at_world(projectile["x"], projectile["y"]) in SOLID_CELLS
                or projectile_hits_tree(projectile["x"], projectile["y"])):
            spawn_particle_burst(projectile["x"], projectile["y"],
                                 projectile["z"], (1.0, 0.08, 0.68), 6, 95.0)
            continue
        player_distance = sqrt(
            (projectile["x"] - player_x) ** 2
            + (projectile["y"] - player_y) ** 2
            + (projectile["z"] - eye_z) ** 2
        )
        if player_distance < 48.0:
            if damage_cooldown <= 0.0:
                player_health -= ANCHOR_PROJECTILE_DAMAGE
                damage_cooldown = 0.75
                damage_flash_timer = 0.48
                camera_shake_timer = 0.20
                set_status("A Rift Anchor projectile struck Aegis-7!", 1.2)
            continue
        remaining.append(projectile)
    enemy_projectiles = remaining


def has_clear_sentry_line(start_x, start_y, target_x, target_y):
    distance = sqrt((target_x - start_x) ** 2 + (target_y - start_y) ** 2)
    steps = max(1, int(distance / 55.0))
    for index in range(1, steps):
        amount = index / float(steps)
        sample_x = start_x + (target_x - start_x) * amount
        sample_y = start_y + (target_y - start_y) * amount
        if (cell_at_world(sample_x, sample_y) in SOLID_CELLS
                or projectile_hits_tree(sample_x, sample_y)):
            return False
    return True


def update_sentries(dt):
    global sentries, player_score
    surviving_sentries = []
    for sentry in sentries:
        sentry["life"] -= dt
        sentry["cooldown"] = max(0.0, sentry["cooldown"] - dt)
        sentry["beam_timer"] = max(0.0, sentry["beam_timer"] - dt)
        if sentry["life"] <= 0.0:
            spawn_particle_burst(sentry["x"], sentry["y"], 42.0,
                                 CYAN_COLOR, 10, 105.0)
            continue

        visible_targets = []
        for enemy in enemies:
            distance_squared = ((enemy["x"] - sentry["x"]) ** 2
                                + (enemy["y"] - sentry["y"]) ** 2)
            if distance_squared > SENTRY_RANGE ** 2:
                continue
            if has_clear_sentry_line(sentry["x"], sentry["y"],
                                     enemy["x"], enemy["y"]):
                visible_targets.append((distance_squared, enemy))
        if visible_targets:
            _, target = min(visible_targets, key=lambda item: item[0])
            desired_heading = degrees(atan2(target["x"] - sentry["x"],
                                            target["y"] - sentry["y"])) % 360.0
            heading_difference = ((desired_heading - sentry["heading"] + 180.0)
                                  % 360.0) - 180.0
            max_turn = 320.0 * dt
            sentry["heading"] = (
                sentry["heading"] + max(-max_turn, min(max_turn, heading_difference))
            ) % 360.0
            if sentry["cooldown"] <= 0.0 and abs(heading_difference) < 28.0:
                target["health"] -= 1
                target["hit_flash"] = 0.14
                target["damaged_timer"] = 1.0
                target["aggro_timer"] = 3.0
                sentry["cooldown"] = 0.82
                sentry["beam_timer"] = 0.13
                sentry["beam_x"] = target["x"]
                sentry["beam_y"] = target["y"]
                sentry["beam_z"] = 92.0
                player_score += 5
                if target["health"] <= 0:
                    spawn_particle_burst(target["x"], target["y"], 88.0,
                                         (0.10, 0.90, 1.0), 18, 185.0)
        surviving_sentries.append(sentry)

    sentries = surviving_sentries
    enemies[:] = [enemy for enemy in enemies if enemy["health"] > 0]


def register_missed_shot(x, y, z):
    global grid_integrity, missed_shots, player_score
    missed_shots += 1
    grid_integrity = max(0, grid_integrity - MISSED_SHOT_DAMAGE)
    player_score = max(0, player_score - 2)
    add_floating_text(x, y, z + 16.0,
                      f"GRID -{MISSED_SHOT_DAMAGE}", (1.0, 0.32, 0.08))
    if missed_shots % 3 == 0:
        set_status("Missed rounds destabilize the Aether Grid.", 1.6)


def damage_rift_anchor(anchor, damage=1):
    global player_score, hit_marker_timer, enemy_spawn_timer
    if not anchor["active"]:
        return False
    anchor["health"] -= damage
    anchor["hit_flash"] = 0.18
    hit_marker_timer = 0.16
    player_score += 15
    add_floating_text(anchor["x"], anchor["y"], 170.0,
                      "+15 ANCHOR", (1.0, 0.34, 0.92))
    spawn_particle_burst(anchor["x"], anchor["y"], 105.0,
                         (0.92, 0.10, 1.0), 9, 145.0)
    if anchor["health"] <= 0:
        anchor["health"] = 0
        anchor["active"] = False
        player_score += 100
        enemy_spawn_timer = 0.0
        spawn_particle_burst(anchor["x"], anchor["y"], 100.0,
                             (1.0, 0.12, 0.70), 28, 230.0)
        destroyed = anchors_destroyed_count()
        set_status(
            f"Rift Anchor destroyed ({destroyed}/3)! Memory shield offline; enemy wave incoming.",
            4.2,
        )
    return True


def update_bullets(dt):
    global player_score, hit_marker_timer
    remaining = []
    for bullet in bullets:
        bullet["prev_x"] = bullet["x"]
        bullet["prev_y"] = bullet["y"]
        bullet["prev_z"] = bullet["z"]
        bullet["x"] += bullet["dx"] * 900.0 * dt
        bullet["y"] += bullet["dy"] * 900.0 * dt
        bullet["life"] -= dt
        if bullet["life"] <= 0.0:
            register_missed_shot(bullet["x"], bullet["y"], bullet["z"])
            continue
        if (cell_at_world(bullet["x"], bullet["y"]) in SOLID_CELLS
                or projectile_hits_tree(bullet["x"], bullet["y"])):
            spawn_particle_burst(bullet["x"], bullet["y"], bullet["z"],
                                 (0.12, 0.82, 1.0), 6, 95.0)
            register_missed_shot(bullet["x"], bullet["y"], bullet["z"])
            continue

        hit_target = False
        for anchor in rift_anchors:
            anchor_distance = sqrt((bullet["x"] - anchor["x"]) ** 2
                                   + (bullet["y"] - anchor["y"]) ** 2)
            if (anchor["active"] and anchor_distance < 62.0
                    and 24.0 < bullet["z"] < 185.0):
                damage_rift_anchor(anchor)
                hit_target = True
                break

        if not hit_target:
            for enemy in enemies:
                distance = sqrt((bullet["x"] - enemy["x"]) ** 2
                                + (bullet["y"] - enemy["y"]) ** 2)
                if distance >= 52.0:
                    continue
                enemy["health"] -= 1
                enemy["hit_flash"] = 0.16
                enemy["damaged_timer"] = 1.4
                enemy["aggro_timer"] = 4.0
                player_score += 10
                hit_marker_timer = 0.16
                add_floating_text(enemy["x"], enemy["y"], 175.0,
                                  "+10", (0.30, 1.0, 0.85))
                if enemy["health"] <= 0:
                    spawn_particle_burst(enemy["x"], enemy["y"], 82.0,
                                         (1.0, 0.14, 0.035), 22, 205.0)
                    spawn_particle_burst(enemy["x"], enemy["y"], 96.0,
                                         MAGENTA_COLOR, 12, 145.0)
                else:
                    spawn_particle_burst(bullet["x"], bullet["y"], bullet["z"],
                                         (1.0, 0.35, 0.06), 7, 120.0)
                hit_target = True
                break
        if not hit_target:
            remaining.append(bullet)

    bullets[:] = remaining
    enemies[:] = [enemy for enemy in enemies if enemy["health"] > 0]


def update_enemies(dt):
    global player_health, core_health, damage_cooldown, core_damage_cooldown
    global damage_flash_timer, camera_shake_timer
    for enemy in enemies:
        enemy["pulse"] += dt * 5.0
        enemy["attack_cooldown"] = max(0.0, enemy["attack_cooldown"] - dt)
        enemy["attack_animation"] = max(0.0, enemy["attack_animation"] - dt)
        enemy["aggro_timer"] = max(0.0, enemy["aggro_timer"] - dt)
        enemy["hit_flash"] = max(0.0, enemy["hit_flash"] - dt)
        enemy["damaged_timer"] = max(0.0, enemy["damaged_timer"] - dt)
        enemy["stun_timer"] = max(0.0, enemy["stun_timer"] - dt)
        if enemy["stun_timer"] > 0.0:
            continue
        player_delta_x = player_x - enemy["x"]
        player_delta_y = player_y - enemy["y"]
        player_distance = sqrt(player_delta_x ** 2 + player_delta_y ** 2)
        core_delta_x = core_position[0] - enemy["x"]
        core_delta_y = core_position[1] - enemy["y"]
        core_distance = sqrt(core_delta_x ** 2 + core_delta_y ** 2)
        target_player = (enemy["aggro_timer"] > 0.0
                         or player_distance < min(680.0, enemy["detection_range"]))
        if target_player:
            target_x, target_y = player_x, player_y
        else:
            target_x, target_y = core_position

        waypoint_x, waypoint_y = navigation_waypoint(
            enemy["x"], enemy["y"], target_x, target_y
        )
        delta_x = waypoint_x - enemy["x"]
        delta_y = waypoint_y - enemy["y"]
        waypoint_distance = sqrt(delta_x * delta_x + delta_y * delta_y)

        # #######Turn through the shortest angle while keeping heading in 0..360.
        look_delta_x = delta_x if waypoint_distance > 0.001 else target_x - enemy["x"]
        look_delta_y = delta_y if waypoint_distance > 0.001 else target_y - enemy["y"]
        if abs(look_delta_x) + abs(look_delta_y) > 0.001:
            desired_heading = degrees(atan2(look_delta_x, look_delta_y)) % 360.0
            heading_difference = ((desired_heading - enemy["heading"] + 180.0)
                                  % 360.0) - 180.0
            maximum_turn = ENEMY_TURN_SPEED * dt
            heading_step = max(-maximum_turn,
                               min(maximum_turn, heading_difference))
            enemy["heading"] = (enemy["heading"] + heading_step) % 360.0

        if waypoint_distance > 0.001:
            pressure_speed = (1.0 + min(0.42, elapsed_game_time / 190.0)
                              + anchors_destroyed_count() * 0.07
                              + (0.18 if core_upload_active else 0.0))
            speed = enemy["speed"] * pressure_speed
            move_x = delta_x / waypoint_distance * speed * dt
            move_y = delta_y / waypoint_distance * speed * dt
            if not is_blocked(enemy["x"] + move_x, enemy["y"]):
                enemy["x"] += move_x
            if not is_blocked(enemy["x"], enemy["y"] + move_y):
                enemy["y"] += move_y

        if target_player and player_distance < 76.0 and enemy["attack_cooldown"] <= 0.0:
            begin_enemy_attack(enemy)
            if damage_cooldown <= 0.0:
                player_health -= enemy["damage"]
                damage_cooldown = 1.0
                damage_flash_timer = 0.65
                camera_shake_timer = 0.32
                set_status("A Rift Beast attacked you!", 1.0)
            enemy["attack_cooldown"] = enemy["attack_interval"]
        elif (not target_player and core_distance < 108.0
              and enemy["attack_cooldown"] <= 0.0):
            begin_enemy_attack(enemy)
            if core_damage_cooldown <= 0.0:
                core_health = max(0, core_health - enemy["core_damage"])
                core_damage_cooldown = 1.45
                spawn_particle_burst(core_position[0], core_position[1], 82.0,
                                     (1.0, 0.16, 0.04), 8, 115.0)
                if status_message_timer < 0.4:
                    set_status("Rift Beasts are damaging the Grid Core!", 1.2)
            enemy["attack_cooldown"] = enemy["attack_interval"]


def update_enemy_spawning(dt):
    global enemy_spawn_timer, enemy_spawn_cursor
    if core_upload_active:
        target_count = MAX_ACTIVE_ENEMIES
    else:
        target_count = min(
            MAX_ACTIVE_ENEMIES,
            INITIAL_ACTIVE_ENEMIES + int(elapsed_game_time / 24.0)
            + anchors_destroyed_count() * 2,
        )
    enemy_spawn_timer -= dt
    if len(enemies) >= target_count or enemy_spawn_timer > 0.0:
        return

    spawned = False
    for _ in range(len(enemy_spawn_points)):
        spawn_index = enemy_spawn_cursor % len(enemy_spawn_points)
        enemy_spawn_cursor += 1
        spawn_x, spawn_y = enemy_spawn_points[spawn_index]
        if (spawn_x - player_x) ** 2 + (spawn_y - player_y) ** 2 < 430.0 ** 2:
            continue
        enemies.append(create_enemy(spawn_index))
        spawned = True
        break

    if spawned:
        if core_upload_active:
            enemy_spawn_timer = 1.35
        else:
            enemy_spawn_timer = max(2.4, 6.2 - elapsed_game_time * 0.024)
    else:
        enemy_spawn_timer = 1.0


def update_hazards(dt):
    global player_health, damage_cooldown, damage_flash_timer, camera_shake_timer
    row, col = cell_indices_from_world(player_x, player_y)
    if not (0 <= row < MAP_H and 0 <= col < MAP_W):
        return
    spikes_are_up = grid[row][col] == "h" and trap_extension(row, col) > 0.58
    if (spikes_are_up and player_z < 52.0 and damage_cooldown <= 0.0):
        player_health -= 22
        damage_cooldown = 0.9
        damage_flash_timer = 0.55
        camera_shake_timer = 0.24
        set_status("Spike trap hit! Time the cycle or jump over it.", 1.4)


def update_pickups():
    global player_score, energy_collected, checkpoint_x, checkpoint_y

    for crystal in crystals:
        if crystal["taken"]:
            continue
        distance = sqrt((player_x - crystal["x"]) ** 2
                        + (player_y - crystal["y"]) ** 2)
        anchor = rift_anchors[crystal["anchor_index"]]
        if distance < 82.0 and anchor["active"]:
            set_status(
                f"Memory shielded: destroy this Rift Anchor ({anchor['health']} HP).",
                1.2,
            )
            continue
        if distance < 70.0:
            crystal["taken"] = True
            energy_collected += 1
            player_score += 50
            checkpoint_x, checkpoint_y = player_x, player_y
            remaining = max(0, ENERGY_REQUIRED - energy_collected)
            if remaining:
                set_status(
                    f"ECHO memory recovered. {remaining} crystal(s) remain.", 2.4
                )
            else:
                set_status("Core energy restored! Return to the Grid Core.", 4.5)


def respawn_player():
    global player_x, player_y, player_z, vertical_velocity
    global player_health, player_lives, damage_cooldown, game_state
    player_lives -= 1
    if player_lives <= 0:
        player_lives = 0
        game_state = "game_over"
        set_status("The Guardian has fallen.", 5.0)
        return
    player_x, player_y = checkpoint_x, checkpoint_y
    player_z = 0.0
    vertical_velocity = 0.0
    player_health = 100
    damage_cooldown = 2.0
    set_status("Respawned at the latest checkpoint.", 3.0)


def update_objective(dt):
    global game_state, player_score, core_activated
    global core_upload_active, core_upload_progress, enemy_spawn_timer
    global checkpoint_x, checkpoint_y
    if core_health <= 0:
        game_state = "game_over"
        set_status("The Grid Core was destroyed by the Rift Beasts.", 8.0)
        return
    if grid_integrity <= 0:
        game_state = "game_over"
        set_status("Too many missed rounds collapsed the Aether Grid.", 8.0)
        return
    if energy_collected >= ENERGY_REQUIRED and not core_activated:
        distance = sqrt((player_x - core_position[0]) ** 2
                        + (player_y - core_position[1]) ** 2)
        if not core_upload_active and distance < 135.0:
            core_upload_active = True
            core_upload_progress = 0.0
            checkpoint_x, checkpoint_y = core_position
            enemy_spawn_timer = 0.0
            set_status(
                "FINAL CORE LINK STARTED: defend the Core and stay inside the signal radius!",
                5.0,
            )

        if core_upload_active and distance <= CORE_UPLOAD_RADIUS:
            core_upload_progress = min(
                CORE_UPLOAD_DURATION, core_upload_progress + dt
            )
        elif core_upload_active:
            core_upload_progress = max(0.0, core_upload_progress - dt * 0.45)
            if status_message_timer <= 0.2:
                set_status("Core link paused: return to the green signal radius.", 1.4)

        if core_upload_progress >= CORE_UPLOAD_DURATION:
            core_activated = True
            player_score += 400
            game_state = "ending_choice"
            set_status("ECHO is awake. Choose humanity's future: press 1 or 2.", 10.0)


def update_visual_effects(dt):
    global particles, floating_texts, muzzle_flash_timer, weapon_recoil
    global hit_marker_timer, damage_flash_timer, camera_shake_timer
    global emp_cooldown, emp_effect_timer

    muzzle_flash_timer = max(0.0, muzzle_flash_timer - dt)
    weapon_recoil = max(0.0, weapon_recoil - dt * 6.5)
    hit_marker_timer = max(0.0, hit_marker_timer - dt)
    damage_flash_timer = max(0.0, damage_flash_timer - dt)
    camera_shake_timer = max(0.0, camera_shake_timer - dt)
    emp_cooldown = max(0.0, emp_cooldown - dt)
    emp_effect_timer = max(0.0, emp_effect_timer - dt)

    alive_particles = []
    for particle in particles:
        particle["life"] -= dt
        if particle["life"] <= 0.0:
            continue
        particle["x"] += particle["vx"] * dt
        particle["y"] += particle["vy"] * dt
        particle["z"] += particle["vz"] * dt
        particle["vz"] -= 260.0 * dt
        alive_particles.append(particle)
    particles = alive_particles

    alive_texts = []
    for item in floating_texts:
        item["life"] -= dt
        if item["life"] <= 0.0:
            continue
        item["z"] += 32.0 * dt
        alive_texts.append(item)
    floating_texts = alive_texts


def update_game(dt):
    global elapsed_game_time, damage_cooldown, core_damage_cooldown
    global status_message_timer
    if game_state != "playing":
        return
    elapsed_game_time += dt
    damage_cooldown = max(0.0, damage_cooldown - dt)
    core_damage_cooldown = max(0.0, core_damage_cooldown - dt)
    status_message_timer = max(0.0, status_message_timer - dt)
    update_visual_effects(dt)
    update_player_navigation(dt)
    update_vertical_motion(dt)
    update_rift_anchors(dt)
    update_bullets(dt)
    update_enemy_projectiles(dt)
    update_sentries(dt)
    update_enemies(dt)
    update_enemy_spawning(dt)
    update_hazards(dt)
    update_pickups()
    update_objective(dt)
    if game_state == "playing" and player_health <= 0:
        respawn_player()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, window_width, window_height)
    setup_camera()
    draw_sky()
    enable_world_rendering()
    draw_map()
    draw_core()
    draw_core_activation_beacon()
    draw_rift_anchors()
    draw_crystals()
    draw_sentries()
    for enemy in enemies:
        draw_enemy(enemy)
    draw_bullets()
    draw_enemy_projectiles()
    draw_emp_effect()
    draw_particles()
    draw_floating_texts()
    glDisable(GL_FOG)
    draw_first_person_hands()

    draw_crosshair()
    draw_hud()
    glutSwapBuffers()


def idle():
    global last_frame_time
    current_time = time.perf_counter()
    if last_frame_time == 0.0:
        last_frame_time = current_time
    dt = min(current_time - last_frame_time, 0.05)
    last_frame_time = current_time
    display_dt = dt
    update_game(display_dt)
    glutPostRedisplay()


def main():
    global quadric, key_up_callbacks_enabled
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(80, 40)
    glutCreateWindow(b"Neon Rift: The Last Guardian")
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glClearColor(*SKY_TOP_COLOR, 1.0)
    quadric = gluNewQuadric()
    reset_game()

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)

    try:
        glutKeyboardUpFunc(keyboard_up_listener)
        glutSpecialUpFunc(special_key_up_listener)
        key_up_callbacks_enabled = True
    except Exception:
        key_up_callbacks_enabled = False
    glutMouseFunc(mouse_listener)
    glutMainLoop()


if __name__ == "__main__":
    main()
