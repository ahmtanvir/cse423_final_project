from math import atan2, cos, degrees, radians, sin, sqrt
from random import uniform, seed
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import time



WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
GRID_LENGTH = 600
GRID_STEP = 60
MAX_ENEMIES = 5
BOUNDARY_HEIGHT = 70
PLAYER_RADIUS = 32
ENEMY_RADIUS = 42
BULLET_SPEED = 720.0
ENEMY_SPEED = 48.0
CHEAT_ROTATION_SPEED = 130.0


field_of_view = 90
camera_position = (0.0,-850.0,600.0)
camera_angle = 0.0
camera_height = 600.0
is_first_person_view = False

player_position_x = 0.0
player_position_y = 0.0
player_gun_angle = 0.0
remaining_player_lives = 5
player_score = 0
missed_bullet_count = 0
is_game_over = False

is_cheat_mode = False
is_auto_camera_enabled = False
automatic_fire_cooldown = 0.0
previous_frame_timestamp = 0
shared_quadric = None
active_bullets = []
active_enemies = []
seed(400)

def create_enemy():
    while True:
        spawn_position_x = uniform(-GRID_LENGTH + 70, GRID_LENGTH - 70)
        spawn_position_y = uniform(-GRID_LENGTH + 70, GRID_LENGTH - 70)
        if ((spawn_position_x - player_position_x) ** 2 + (spawn_position_y - player_position_y) ** 2 > 260 ** 2):
            return {
                "position_x": spawn_position_x,
                "position_y": spawn_position_y,
                "pulse_phase": uniform(0.0, 6.28),
            }


def reset_game():
    global player_position_x, player_position_y, player_gun_angle
    global remaining_player_lives, player_score, missed_bullet_count
    global is_game_over, active_bullets, active_enemies
    global automatic_fire_cooldown
    player_position_x = 0.0
    player_position_y = 0.0
    player_gun_angle = 0.0
    remaining_player_lives = 5
    player_score = 0
    missed_bullet_count = 0
    is_game_over = False
    active_bullets = []
    active_enemies = [create_enemy() for _ in range(MAX_ENEMIES)]
    automatic_fire_cooldown = 0.0


def clamp_player_to_grid():
    global player_position_x, player_position_y
    limit = GRID_LENGTH - 55
    player_position_x = max(-limit, min(limit, player_position_x))
    player_position_y = max(-limit, min(limit, player_position_y))

def wrap_angle(angle):
    return angle % 360.0

def shortest_angle_difference(target, current):
    return (target - current + 180.0) % 360.0 - 180.0

def forward_vector(angle):
    angle_radians = radians(angle)
    return sin(angle_radians), cos(angle_radians)

def draw_text(screen_position_x, screen_position_y, message,
              font=GLUT_BITMAP_HELVETICA_18, text_color=(1.0, 1.0, 1.0)):
    glColor3f(*text_color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(screen_position_x, screen_position_y)



    for character in str(message):glutBitmapCharacter(font, ord(character))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)




def draw_cylinder(cylinder_radius, cylinder_height, surface_color,slice_count=16, stack_count=8):
    glColor3f(*surface_color)
    gluCylinder(shared_quadric, cylinder_radius, cylinder_radius,cylinder_height, slice_count, stack_count)


def draw_cube(cube_size, surface_color):
    glColor3f(*surface_color)
    glutSolidCube(cube_size)

def draw_boundary(boundary_center_x, boundary_center_y,boundary_scale_x, boundary_scale_y, wall_color):
    glPushMatrix()
    glTranslatef(boundary_center_x, boundary_center_y, BOUNDARY_HEIGHT / 2.0)
    glScalef(boundary_scale_x, boundary_scale_y, BOUNDARY_HEIGHT)
    draw_cube(1.0, wall_color)
    glPopMatrix()


def draw_dynamic_grid():
    floor_color_palette = [
        (0.02, 0.02, 0.02),
        (0.92, 0.92, 0.92),]
    
    grid_coordinates = range(-GRID_LENGTH, GRID_LENGTH, GRID_STEP)

    for tile_row_index, tile_start_y in enumerate(grid_coordinates):
        for tile_column_index, tile_start_x in enumerate(grid_coordinates):
            selected_floor_color = floor_color_palette[
                (tile_row_index + tile_column_index) % len(floor_color_palette)]
            glColor3f(*selected_floor_color)
            glBegin(GL_QUADS)
            glVertex3f(tile_start_x, tile_start_y, 0)
            glVertex3f(tile_start_x + GRID_STEP, tile_start_y, 0)
            glVertex3f(tile_start_x + GRID_STEP, tile_start_y + GRID_STEP, 0)
            glVertex3f(tile_start_x, tile_start_y + GRID_STEP, 0)
            glEnd()


    glBegin(GL_LINES)
    grid_line_palette = [
        (0.95, 0.35, 0.55),
        (0.25, 0.95, 0.85),
        (1.00, 0.78, 0.25),
        (0.70, 0.45, 1.00),
    ]

    for line_index, coordinate in enumerate(
            range(-GRID_LENGTH, GRID_LENGTH + 1, GRID_STEP)):
        glColor3f(*grid_line_palette[line_index % len(grid_line_palette)])
        glVertex3f(coordinate, -GRID_LENGTH, 0.0)
        glVertex3f(coordinate, GRID_LENGTH, 0.0)
        glVertex3f(-GRID_LENGTH, coordinate, 0.0)
        glVertex3f(GRID_LENGTH, coordinate, 0.0)

    glEnd()
    draw_boundary(-GRID_LENGTH, 0, 12, GRID_LENGTH * 2, (0.90, 0.18, 0.38))
    draw_boundary(GRID_LENGTH, 0, 12, GRID_LENGTH * 2, (0.10, 0.75, 0.95))
    draw_boundary(0, -GRID_LENGTH, GRID_LENGTH * 2, 12, (1.00, 0.48, 0.12))
    draw_boundary(0, GRID_LENGTH, GRID_LENGTH * 2, 12, (0.25, 0.85, 0.35))



def draw_player():
    glPushMatrix()
    glTranslatef(player_position_x, player_position_y, 0)
    if is_game_over:
        glRotatef(90, 1, 0, 0)
    glRotatef(player_gun_angle, 0, 0, 1)

    glPushMatrix()
    glTranslatef(0, 0, 78)
    glScalef(1.10, 0.72, 1.35)
    draw_cube(48, (0.28, 0.40, 0.18))
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 145)
    glColor3f(0.01, 0.01, 0.01)
    gluSphere(shared_quadric, 28, 16, 12)
    glPopMatrix()

    for leg_side_x in (-17, 17):
        glPushMatrix()
        glTranslatef(leg_side_x, 0, 18)
        leg_tilt_angle = -8 if leg_side_x < 0 else 8
        glRotatef(leg_tilt_angle, 0, 1, 0)
        draw_cylinder(10, 58, (0.02, 0.08, 0.95))
        glPopMatrix()

    for arm_side_x in (-32, 32):
        glPushMatrix()
        glTranslatef(arm_side_x, 0, 98)
        arm_direction_angle = -90 if arm_side_x < 0 else 90
        glRotatef(arm_direction_angle, 0, 1, 0)
        draw_cylinder(8, 30, (0.86, 0.68, 0.48))
        glPopMatrix()

        glPushMatrix()
        glTranslatef(arm_side_x * 1.35, 0, 98)
        glColor3f(0.95, 0.76, 0.56)
        gluSphere(shared_quadric, 14, 12, 10)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 55, 96)
    glScalef(0.26, 1.8, 0.26)
    draw_cube(24, (0.72, 0.72, 0.68))
    glPopMatrix()
    glPopMatrix()



def draw_enemy(enemy_data):
    enemy_pulse_scale = 1.0 + 0.16 * sin(enemy_data["pulse_phase"])
    glPushMatrix()
    glTranslatef(enemy_data["position_x"], enemy_data["position_y"], 0)
    glScalef(enemy_pulse_scale, enemy_pulse_scale, enemy_pulse_scale)
    glPushMatrix()
    glTranslatef(0, 0, 38)
    glColor3f(0.90, 0.12, 0.16)
    gluSphere(shared_quadric, 30, 16, 12)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 80)
    glColor3f(1.0, 0.48, 0.12)
    gluSphere(shared_quadric, 22, 16, 12)
    glPopMatrix()
    glPopMatrix()


def draw_bullet(bullet_data):
    glPushMatrix()
    glTranslatef(bullet_data["position_x"], bullet_data["position_y"],
                 bullet_data["position_z"])
    glRotatef(bullet_data["travel_angle"], 0, 0, 1)
    glScalef(0.5, 1.0, 0.5)
    draw_cube(14, (1.0, 0.86, 0.08))
    glPopMatrix()


def fire_bullet():
    bullet_direction_x, bullet_direction_y = forward_vector(player_gun_angle)
    active_bullets.append({
        "position_x": player_position_x + bullet_direction_x * 52,
        "position_y": player_position_y + bullet_direction_y * 52,
        "position_z": 68.0,
        "direction_x": bullet_direction_x,
        "direction_y": bullet_direction_y,
        "travel_angle": player_gun_angle,
    })


def respawn_enemy(enemy_data):
    replacement_enemy_data = create_enemy()
    enemy_data.update(replacement_enemy_data)

def is_bullet_inside_grid(bullet_data):
    return (-GRID_LENGTH - 20 <= bullet_data["position_x"] <= GRID_LENGTH + 20 and -GRID_LENGTH - 20 <= bullet_data["position_y"] <= GRID_LENGTH + 20
    )

def update_bullets(elapsed_seconds):
    global player_score, missed_bullet_count, is_game_over
    bullets_remaining_after_update = []
    for bullet_data in active_bullets:
        bullet_data["position_x"] += (bullet_data["direction_x"]* BULLET_SPEED * elapsed_seconds)
        bullet_data["position_y"] += (bullet_data["direction_y"]* BULLET_SPEED * elapsed_seconds)
        did_bullet_hit_enemy = False


        for enemy_data in active_enemies:
            distance_to_enemy = sqrt(
                (bullet_data["position_x"] - enemy_data["position_x"]) ** 2
                + (bullet_data["position_y"] - enemy_data["position_y"]) ** 2
            )

            if distance_to_enemy <= ENEMY_RADIUS:
                player_score += 1
                respawn_enemy(enemy_data)
                did_bullet_hit_enemy = True
                break
        if did_bullet_hit_enemy:
            continue
        if is_bullet_inside_grid(bullet_data):
            bullets_remaining_after_update.append(bullet_data)
        else:
            missed_bullet_count += 1
            if missed_bullet_count >= 10:
                is_game_over = True
    active_bullets[:] = bullets_remaining_after_update




def update_enemies(elapsed_seconds):
    global remaining_player_lives, is_game_over

    for enemy_data in active_enemies:
        enemy_data["pulse_phase"] += elapsed_seconds * 5.0
        movement_vector_x = player_position_x - enemy_data["position_x"]
        movement_vector_y = player_position_y - enemy_data["position_y"]
        distance_to_player = sqrt(movement_vector_x ** 2 + movement_vector_y ** 2)


        if distance_to_player <= PLAYER_RADIUS + ENEMY_RADIUS * 0.55:
            remaining_player_lives -= 1
            respawn_enemy(enemy_data)
            if remaining_player_lives <= 0:
                remaining_player_lives = 0
                is_game_over = True
            continue
        if distance_to_player > 0.001:
            enemy_data["position_x"] += (movement_vector_x / distance_to_player* ENEMY_SPEED * elapsed_seconds)
            enemy_data["position_y"] += (movement_vector_y / distance_to_player* ENEMY_SPEED * elapsed_seconds)


def find_enemy_in_line_of_sight():
    closest_visible_enemy = None
    closest_enemy_distance = float("inf")
    for enemy_data in active_enemies:
        direction_to_enemy_x = enemy_data["position_x"] - player_position_x
        direction_to_enemy_y = enemy_data["position_y"] - player_position_y
        distance_to_enemy = sqrt(direction_to_enemy_x ** 2 + direction_to_enemy_y ** 2)
        target_enemy_angle = degrees(atan2(direction_to_enemy_x,direction_to_enemy_y)) % 360.0
        angle_difference = abs(shortest_angle_difference(target_enemy_angle,player_gun_angle))
        if angle_difference <= 11.0 and distance_to_enemy < closest_enemy_distance:
            closest_visible_enemy = enemy_data
            closest_enemy_distance = distance_to_enemy
    return closest_visible_enemy

def update_cheat_mode(elapsed_seconds):
    global player_gun_angle, automatic_fire_cooldown
    if not is_cheat_mode or is_game_over:
        return
    player_gun_angle = wrap_angle(player_gun_angle+ CHEAT_ROTATION_SPEED * elapsed_seconds)
    automatic_fire_cooldown -= elapsed_seconds

    if (automatic_fire_cooldown <= 0.0
            and find_enemy_in_line_of_sight() is not None):
        fire_bullet()
        automatic_fire_cooldown = 0.18


def update_game(elapsed_seconds):
    if is_game_over:
        return
    update_cheat_mode(elapsed_seconds)
    update_bullets(elapsed_seconds)
    update_enemies(elapsed_seconds)


def keyboard_listener(pressed_key, mouse_position_x, mouse_position_y):
    global player_position_x, player_position_y, player_gun_angle
    global is_cheat_mode, is_auto_camera_enabled
    pressed_key = pressed_key.lower()
    if pressed_key == b"r" and is_game_over:
        reset_game()
        return
    if is_game_over:
        return
    player_movement_step = 22.0
    if pressed_key == b"w":
        movement_direction_x, movement_direction_y = forward_vector(player_gun_angle)
        player_position_x += movement_direction_x * player_movement_step
        player_position_y += movement_direction_y * player_movement_step
        clamp_player_to_grid()
    elif pressed_key == b"s":
        movement_direction_x, movement_direction_y = forward_vector(player_gun_angle)
        player_position_x -= movement_direction_x * player_movement_step
        player_position_y -= movement_direction_y * player_movement_step
        clamp_player_to_grid()
    elif pressed_key == b"a" and not is_cheat_mode:
        player_gun_angle = wrap_angle(player_gun_angle - 7.0)
    elif pressed_key == b"d" and not is_cheat_mode:
        player_gun_angle = wrap_angle(player_gun_angle + 7.0)
    elif pressed_key == b"c":
        is_cheat_mode = not is_cheat_mode
        if not is_cheat_mode:
            is_auto_camera_enabled = False
    elif pressed_key == b"v":
        if is_cheat_mode and is_first_person_view:
            is_auto_camera_enabled = not is_auto_camera_enabled

def special_key_listener(pressed_special_key, mouse_position_x, mouse_position_y):
    global camera_height, camera_angle
    if pressed_special_key == GLUT_KEY_UP:
        camera_height = min(1050.0, camera_height + 18.0)
    elif pressed_special_key == GLUT_KEY_DOWN:
        camera_height = max(180.0, camera_height - 18.0)
    elif pressed_special_key == GLUT_KEY_LEFT:
        camera_angle -= 5.0
    elif pressed_special_key == GLUT_KEY_RIGHT:
        camera_angle += 5.0


def mouse_listener(mouse_button, mouse_state, mouse_position_x, mouse_position_y):
    global is_first_person_view, is_auto_camera_enabled
    if mouse_state != GLUT_DOWN:
        return
    if mouse_button == GLUT_LEFT_BUTTON and not is_game_over:
        fire_bullet()
    elif mouse_button == GLUT_RIGHT_BUTTON:
        is_first_person_view = not is_first_person_view
        if not is_first_person_view:
            is_auto_camera_enabled = False

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(field_of_view, WINDOW_WIDTH / float(WINDOW_HEIGHT), 0.1, 2200.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


    if is_first_person_view:
        camera_direction_x, camera_direction_y = forward_vector(
            player_gun_angle if (not is_cheat_mode or is_auto_camera_enabled) else 0.0
        )
        first_person_eye_x = player_position_x + camera_direction_x * 24.0
        first_person_eye_y = player_position_y + camera_direction_y * 24.0
        first_person_eye_z = 105.0
        first_person_look_x = first_person_eye_x + camera_direction_x * 220.0
        first_person_look_y = first_person_eye_y + camera_direction_y * 220.0
        gluLookAt(first_person_eye_x, first_person_eye_y, first_person_eye_z,first_person_look_x, first_person_look_y, 55.0, 0, 0, 1)
        return


    angle_radians = radians(camera_angle)
    orbit_radius = 850.0
    third_person_eye_x = player_position_x + sin(angle_radians) * orbit_radius
    third_person_eye_y = player_position_y - cos(angle_radians) * orbit_radius
    gluLookAt(third_person_eye_x, third_person_eye_y, camera_height,player_position_x, player_position_y, 0, 0, 0, 1)


def draw_hud():
    draw_text(18, 770, f"Lives: {remaining_player_lives}   Score: {player_score}   Bullets Missed: {missed_bullet_count}/10")
    camera_mode_label = "FIRST-PERSON" if is_first_person_view else "THIRD-PERSON"
    cheat_mode_label = "ON" if is_cheat_mode else "OFF"
    auto_camera_label = "ON" if is_auto_camera_enabled else "OFF"
    draw_text(18, 742, f"Camera: {camera_mode_label}   Cheat: {cheat_mode_label}   Auto-Camera: {auto_camera_label}")
    draw_text(18, 714, "W/S Move   A/D Aim   Left Click Fire   Right Click Camera   C Cheat   V Auto-Camera   R Restart")

    if is_game_over:
        draw_text(350, 420, "GAME OVER", GLUT_BITMAP_HELVETICA_18, (1.0, 0.18, 0.18))
        draw_text(300, 385, "Press R to restart", GLUT_BITMAP_HELVETICA_18, (1.0, 0.9, 0.2))


def show_screen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    setup_camera()

    draw_dynamic_grid()
    draw_player()
    for enemy_data in active_enemies:
        draw_enemy(enemy_data)
    for bullet_data in active_bullets:
        draw_bullet(bullet_data)
    draw_hud()
    glutSwapBuffers()


def idle():
    global previous_frame_timestamp
    current_frame_timestamp = time.perf_counter()
    if previous_frame_timestamp == 0:previous_frame_timestamp = current_frame_timestamp
    elapsed_seconds = min(current_frame_timestamp - previous_frame_timestamp, 0.05)
    previous_frame_timestamp = current_frame_timestamp
    update_game(elapsed_seconds)
    glutPostRedisplay()

def main():
    global shared_quadric
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"OpenGL Grid Survival Game")
    shared_quadric = gluNewQuadric()
    reset_game()
    glutDisplayFunc(show_screen)
    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)
    glutIdleFunc(idle)
    glutMainLoop()


if __name__ == "__main__":
    main()
