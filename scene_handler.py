from beatmap_reader import *
#from hand_tracking import *
import pyglet
import time
from pyglet.gl import *
import cv2
import numpy as np
from PIL import Image
import mediapipe as mp
import threading
import copy

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

osu_file_name = 'gurenge'
beatmap = read_beatmap(osu_file_name+'.osu')
bgm = pyglet.resource.media(osu_file_name+'.mp3')
hit_sound = pyglet.media.load('hit.wav', streaming=False)
# hit_sound_player = pyglet.media.Player()
# hit_sound_player.queue(hit_sound)
# hit_sound_player.volume = 0.2
osu_w = 640
osu_h = 480

WIDTH = 1280
HEIGHT = 720
RADIUS = 50
T_START = -2000 # Ellapse time of hitpoints
T_END = 5

window = pyglet.window.Window(width=WIDTH, height=HEIGHT)
circle_batch = pyglet.graphics.Batch()
outer_batch = pyglet.graphics.Batch()
cursor_batch1 = pyglet.graphics.Batch()
cursor_batch2 = pyglet.graphics.Batch()
score_batch = pyglet.graphics.Batch()

start_time = time.time()*1000

def hit_judge(ptx, pty, cursorx, cursory):
    return (ptx-cursorx)**2+(pty-cursory)**2 < RADIUS**2

score=0
score_label = pyglet.text.Label('Score: '+str(score),
                          font_name='Arial',
                          font_size=36,
                          x=WIDTH*0.9, y=HEIGHT*0.95,
                          anchor_x='center', anchor_y='center', color=(0,0,0,255))
hit_label = pyglet.text.Label('',font_name='Arial', font_size=20, bold=True,
                                    x=0, y=0,
                                    anchor_x='center', anchor_y='center', color=(0, 255, 0, 255))

score_background = pyglet.shapes.Rectangle(WIDTH*0.8, HEIGHT*0.9,300,100)
score_background.opacity = 200

i1 = 0
cursor_left1 = None
cursor_left2 = None
cursor_right1 = None
cursor_right2 = None
def update_circle(dt):
    global i1, cursor_left1,cursor_left2, cursor_right1, cursor_right2, score, score_label, hit_label
    t = time.time()*1000 - start_time
    cursor_left1 = pyglet.shapes.Circle(left_hand_pos[0], left_hand_pos[1], 15, color=(0,0,255),batch=cursor_batch1)
    cursor_left2 = pyglet.shapes.Circle(left_hand_pos[0], left_hand_pos[1], 20, color=(255,255,255),batch=cursor_batch2)
    cursor_right1 = pyglet.shapes.Circle(right_hand_pos[0], right_hand_pos[1], 15, color=(255,0,0),batch=cursor_batch1)
    cursor_right2 = pyglet.shapes.Circle(right_hand_pos[0], right_hand_pos[1], 20, color=(255,255,255),batch=cursor_batch2)
    for i in range(i1, len(beatmap)):
        hitpoint = beatmap[i]
        gen_time = int(hitpoint['time'])
        if t < gen_time + T_START:
            break
        elif t > gen_time + T_END:
            pt_x = int(hitpoint['x'])/osu_w*WIDTH+100
            pt_y = int(hitpoint['y'])/osu_h*HEIGHT+50
            if (hit_judge(pt_x, pt_y, left_hand_pos[0], left_hand_pos[1])
               or hit_judge(pt_x, pt_y, right_hand_pos[0], right_hand_pos[1])):   
                hit_sound.play()
                score += 100
                hit_label = pyglet.text.Label('PERFECT',
                                    font_name='Arial', font_size=20, bold=True,
                                    x=pt_x, y=pt_y,
                                    anchor_x='center', anchor_y='center', color=(0, 255, 0, 255))
            else:
                score -= 10
                hit_label = pyglet.text.Label('MISS',
                                    font_name='Arial', font_size=20, bold=True,
                                    x=pt_x, y=pt_y,
                                    anchor_x='center', anchor_y='center', color=(255, 0, 0, 255))
            score_label = pyglet.text.Label('Score: '+str(score),
                                    font_name='Arial',
                                    font_size=36,
                                    x=WIDTH*0.9, y=HEIGHT*0.95,
                                    anchor_x='center', anchor_y='center', color=(0,0,0,255))
            hitpoint['inner'].delete()
            hitpoint['outer'].delete()
            i1 += 1
            continue
        else:
            x, y = int(hitpoint['x'])/osu_w*WIDTH+100, int(hitpoint['y'])/osu_h*HEIGHT+50
            hitpoint['outer'] = pyglet.shapes.Circle(x, y, RADIUS*(1+(gen_time-t)/2000), color=(255, 255, 0), batch=outer_batch)
            hitpoint['inner'] = pyglet.shapes.Circle(x, y, RADIUS, color=(255, 165, 0), batch=circle_batch)


def cv2glet(img):
    '''Assumes image is in BGR color space. Returns a pyimg object'''
    rows, cols, channels = img.shape
    
    raw_img = Image.fromarray(img).tobytes()

    top_to_bottom_flag = -1
    bytes_per_row = channels*cols
    pyimg = pyglet.image.ImageData(width=cols, 
                                   height=rows, 
                                   format='BGR', 
                                   data=raw_img, 
                                   pitch=top_to_bottom_flag*bytes_per_row)
    pyimg.scale = 2
    return pyimg


cap = cv2.VideoCapture(0)
frame_data = cap.read()
frame_data = frame_data[1]
pyimg = cv2glet(frame_data)
game_running = True

left_hand_pos = [0,0,0]
right_hand_pos = [0,0,0]


def thread_mediapipe():
    global frame_data, left_hand_pos, right_hand_pos
    cap = cv2.VideoCapture(0)
    camera_w = 640*2 # scaled to double
    camera_h = 480*2
    with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:
        while game_running:
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                # If loading a video, use 'break' instead of 'continue'.

            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image)
            # Draw the hand annotations on the image.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            if results.multi_hand_landmarks:
                for i in range(len(results.multi_hand_landmarks)):
                    hand_landmarks = results.multi_hand_landmarks[i]
                    opposite_handedness = results.multi_handedness[i].classification[0].label # opposite due to flip
                    ### Draw the skeleton detected
                    # mp_drawing.draw_landmarks(
                    #     image,
                    #     hand_landmarks,
                    #     mp_hands.HAND_CONNECTIONS,
                    #     mp_drawing_styles.get_default_hand_landmarks_style(),
                    #     mp_drawing_styles.get_default_hand_connections_style())
                    if opposite_handedness == 'Left':
                        right_hand_pos = [camera_w-hand_landmarks.landmark[12].x*camera_w, 
                                    camera_h-hand_landmarks.landmark[12].y*camera_h,
                                    hand_landmarks.landmark[12].z]
                    else:
                        left_hand_pos = [camera_w-hand_landmarks.landmark[12].x*camera_w, 
                                    camera_h-hand_landmarks.landmark[12].y*camera_h,
                                    hand_landmarks.landmark[12].z]
            image = cv2.flip(image, 1)
            if cv2.waitKey(5) & 0xFF == 27:
                print("exiting")
                break
            frame_data = image.copy()
    cap.release()


def update_camera(dt):
    global pyimg
    raw_frame = frame_data
    frame = cv2.resize(raw_frame, None, fx=2, fy=2)
    pyimg = cv2glet(frame)

@window.event()
def on_draw():
    window.clear()
    pyimg.blit(0,0)
    outer_batch.draw()
    circle_batch.draw()
    cursor_batch2.draw()
    cursor_batch1.draw()
    score_background.draw()
    score_label.draw()
    hit_label.draw()
    
@window.event()
def on_close():
    global game_running
    game_running = False
    print("\n-- Game stopping --\n")
    t.join()
    pyglet.app.event_loop.exit()
    return pyglet.event.EVENT_HANDLED

t = threading.Thread(target = thread_mediapipe, name='mediapipe')
t.start()

bgm.play()
start_time = time.time()*1000
pyglet.clock.schedule_interval(update_camera, 1/60)
pyglet.clock.schedule_interval(update_circle, 1/100)
pyglet.app.run()