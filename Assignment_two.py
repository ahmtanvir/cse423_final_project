from OpenGL.GL import *     
from OpenGL.GLUT import *   
from OpenGL.GLU import *    
import random
import time

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 600

PLAYING = 0
PAUSED = 1
GAME_OVER = 2

game_state = PLAYING
score = 0
cheat_mode = False

catcher_center_x = (WINDOW_WIDTH // 2)
catcher_center_y = 30
catcher_w = 40              
catcher_slant = 18          
catcher_h = 16              
catcher_speed = 350.0       
catcher_color = (1.0, 1.0, 1.0)  

diamond_x = 0
diamond_y = 0
diamond_size = 15           
diamond_color = (0.0, 1.0, 0.0)
base_speed = 150.0          
diamond_speed = base_speed

previous_time = time.time()




def get_zone(x0, y0, x1, y1):

    dx = x1 - x0
    dy = y1 - y0
    if abs(dx) >= abs(dy):
        if dx >= 0 and dy >= 0:
            return 0
        elif dx < 0 and dy >= 0:
            return 3
        elif dx < 0 and dy < 0:
            return 4
        else:
            return 7
    else:
        if dx >= 0 and dy >= 0:
            return 1
        elif dx < 0 and dy >= 0:
            return 2
        elif dx < 0 and dy < 0:
            return 5
        else:
            return 6


def to_zone_0(x, y, zone):
    if zone == 0:
        return x, y
    elif zone == 1:
        return y, x
    elif zone == 2:
        return y, -x
    elif zone == 3:
        return -x, y
    elif zone == 4:
        return -x, -y
    elif zone == 5:
        return -y, -x
    elif zone == 6:
        return -y, x
    elif zone == 7:
        return x, -y
    return x, y


def from_zone_0(x, y, zone):
    if zone == 0:
        return x, y
    elif zone == 1:
        return y, x
    elif zone == 2:
        return -y, x
    elif zone == 3:
        return -x, y
    elif zone == 4:
        return -x, -y
    elif zone == 5:
        return -y, -x
    elif zone == 6:
        return y, -x
    elif zone == 7:
        return x, -y
    return x, y


def draw_midpoint_line(x0, y0, x1, y1):


    x0, y0 = int(round(x0)), int(round(y0))
    x1, y1 = int(round(x1)), int(round(y1))

    zone = get_zone(x0, y0, x1, y1)

    x0_z0, y0_z0 = to_zone_0(x0, y0, zone)
    x1_z0, y1_z0 = to_zone_0(x1, y1, zone)

    dx = x1_z0 - x0_z0
    dy = y1_z0 - y0_z0
    d = 2 * dy - dx
    dE = 2 * dy
    dNE = 2 * (dy - dx)

    x, y = x0_z0, y0_z0

    glPointSize(2)             
    glBegin(GL_POINTS)          

    orig_x, orig_y = from_zone_0(x, y, zone)
    glVertex2f(orig_x, orig_y)

    while x < x1_z0:
        if d < 0:
            x += 1
            d += dE
        else:
            x += 1
            y += 1
            d += dNE
        orig_x, orig_y = from_zone_0(x, y, zone)
        glVertex2f(orig_x, orig_y)

    glEnd()                     



def convert_coordinate(x, y):

    game_x = x
    game_y = WINDOW_HEIGHT - y
    return game_x, game_y


def spawn_diamond():
    global diamond_x, diamond_y, diamond_color

    diamond_x = random.randint(30, WINDOW_WIDTH - 30)
    diamond_y = WINDOW_HEIGHT - 20  


    bright_colors = [
        (1.0, 0.2, 0.2),  
        (0.2, 1.0, 0.2),  
        (0.2, 0.6, 1.0),  
        (1.0, 1.0, 0.2),  
        (1.0, 0.2, 1.0),  
        (0.2, 1.0, 1.0),  
        (1.0, 0.6, 0.1)   
    ]
    diamond_color = random.choice(bright_colors)


def restart_game():
    global game_state, score, diamond_speed, catcher_color, catcher_center_x
    score = 0
    diamond_speed = base_speed
    catcher_color = (1.0, 1.0, 1.0)  
    catcher_center_x = WINDOW_WIDTH // 2
    game_state = PLAYING
    spawn_diamond()
    print("Starting Over")




def check_aabb_collision():


    c_min_x = catcher_center_x - (catcher_w + catcher_slant)
    c_max_x = catcher_center_x + (catcher_w + catcher_slant)
    c_min_y = catcher_center_y - 4
    c_max_y = catcher_center_y + catcher_h

    d_min_x = diamond_x - diamond_size
    d_max_x = diamond_x + diamond_size
    d_min_y = diamond_y - diamond_size
    d_max_y = diamond_y + diamond_size

    return (c_min_x < d_max_x and c_max_x > d_min_x and
            c_min_y < d_max_y and c_max_y > d_min_y)




def draw_diamond():

    if game_state == GAME_OVER:
        return  
    glColor3f(*diamond_color)
    r = diamond_size

    draw_midpoint_line(diamond_x, diamond_y + r, diamond_x + r, diamond_y)  
    draw_midpoint_line(diamond_x + r, diamond_y, diamond_x, diamond_y - r)   
    draw_midpoint_line(diamond_x, diamond_y - r, diamond_x - r, diamond_y)
    draw_midpoint_line(diamond_x - r, diamond_y, diamond_x, diamond_y + r)  


def draw_catcher():

    glColor3f(*catcher_color)
    cx = catcher_center_x
    cy = catcher_center_y
    w = catcher_w
    s = catcher_slant
    h = catcher_h

    
    draw_midpoint_line(cx - w - s, cy + h, cx + w + s, cy + h)  
    draw_midpoint_line(cx - w, cy, cx + w, cy)                  
    draw_midpoint_line(cx - w - s, cy + h, cx - w, cy)          
    draw_midpoint_line(cx + w + s, cy + h, cx + w, cy)          


def draw_gui():


    glColor3f(0.0, 1.0, 1.0)
    draw_midpoint_line(75, 560, 45, 560)  
    draw_midpoint_line(45, 560, 60, 575)  
    draw_midpoint_line(45, 560, 60, 545)  


    glColor3f(1.0, 0.75, 0.0)
    
    if game_state == PLAYING:

        draw_midpoint_line(192, 545, 192, 575)
        draw_midpoint_line(208, 545, 208, 575)
    else:
        draw_midpoint_line(190, 545, 190, 575)  
        draw_midpoint_line(190, 575, 215, 560)  
        draw_midpoint_line(190, 545, 215, 560)  

    glColor3f(1.0, 0.0, 0.0)
    draw_midpoint_line(325, 545, 355, 575)  
    draw_midpoint_line(325, 575, 355, 545)  




def keyboard_listener(key, x, y):

    global cheat_mode
    if key == b'c' or key == b'C':
        cheat_mode = not cheat_mode
    glutPostRedisplay()


def special_key_listener(key, x, y):

    global catcher_center_x
    if game_state != PLAYING or cheat_mode:
        return

    step = 25  
    max_w = catcher_w + catcher_slant  

    if key == GLUT_KEY_LEFT:
        catcher_center_x -= step
        if catcher_center_x - max_w < 0:
            catcher_center_x = max_w  

    elif key == GLUT_KEY_RIGHT:
        catcher_center_x += step
        if catcher_center_x + max_w > WINDOW_WIDTH:
            catcher_center_x = WINDOW_WIDTH - max_w 

    glutPostRedisplay()


def mouse_listener(button, state, x, y):
    global game_state
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        game_x, game_y = convert_coordinate(x, y)

        if 530 <= game_y <= 590:
            if 30 <= game_x <= 90:
                restart_game()

            elif 170 <= game_x <= 230:
                if game_state == PLAYING:
                    game_state = PAUSED
                    print("Game Paused")
                elif game_state == PAUSED:
                    game_state = PLAYING
                    print("Game Resumed")

            elif 310 <= game_x <= 370:
                print("Goodbye")
                print(f"Final Score: {score}")
                glutLeaveMainLoop()  

    glutPostRedisplay()




def animate():

    global diamond_y, game_state, score, diamond_speed, catcher_center_x, catcher_color, previous_time

    current_time = time.time()
    dt = current_time - previous_time
    previous_time = current_time

    if dt > 0.1:
        dt = 0.1

    if game_state == PLAYING:
        diamond_y -= diamond_speed * dt

        if cheat_mode:
            diff = diamond_x - catcher_center_x
            if abs(diff) > 1.0:  
                direction = 1 if diff > 0 else -1
                
                dist_y = max(1.0, diamond_y - (catcher_center_y + catcher_h))
                time_to_intercept = max(0.05, dist_y / diamond_speed)
                
                required_speed = (abs(diff) / time_to_intercept) * 1.2
                tracking_speed = max(380.0, required_speed)
                move_step = tracking_speed * dt

                if abs(diff) < move_step:
                    catcher_center_x = diamond_x
                else:
                    catcher_center_x += direction * move_step

                max_w = catcher_w + catcher_slant
                catcher_center_x = max(max_w, min(WINDOW_WIDTH - max_w, catcher_center_x))

        if check_aabb_collision():
            score += 1
            print(f"Score: {score}")
            diamond_speed += 12.0
            spawn_diamond()

        elif diamond_y - diamond_size <= 0:
            game_state = GAME_OVER
            catcher_color = (1.0, 0.0, 0.0)  
            print("Game Over")
            print(f"Final Score: {score}")

    glutPostRedisplay()




def setup_projection():

    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)  
    glMatrixMode(GL_PROJECTION)                    
    glLoadIdentity()                               
    glOrtho(0.0, WINDOW_WIDTH, 0.0, WINDOW_HEIGHT, 0.0, 1.0)  
    glMatrixMode(GL_MODELVIEW)                     


def display():

    glClear(GL_COLOR_BUFFER_BIT)                   
    glLoadIdentity()                               
    setup_projection()                             

    draw_gui()
    draw_catcher()
    draw_diamond()

    glutSwapBuffers()                              




def main():
    glutInit()                                    
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE)   
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)               
    glutCreateWindow(b"Catch the Diamonds! - Midpoint Algorithm")  

    spawn_diamond()

    glutDisplayFunc(display)                       
    glutIdleFunc(animate)                          
    glutKeyboardFunc(keyboard_listener)            
    glutSpecialFunc(special_key_listener)          
    glutMouseFunc(mouse_listener)                  

    glutMainLoop()                                 


if __name__ == "__main__":
    main()