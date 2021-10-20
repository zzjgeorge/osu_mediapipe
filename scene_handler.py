from beatmap_reader import *
#from hand_tracking import *
import pyglet
import time
from pyglet.gl import *
import cv2
import numpy as np
from PIL import Image
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

beatmap = read_beatmap('freedomdive.osu')
bgm = pyglet.resource.media('freedomdive.mp3')
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

start_time = time.time()*1000

i1 = 0
def update_circle(dt):
    global i1
    t = time.time()*1000 - start_time
    for i in range(i1, len(beatmap)):
        hitpoint = beatmap[i]
        gen_time = int(hitpoint['time'])
        if t < gen_time + T_START:
            break
        elif t > gen_time + T_END:
            hit_sound.play()
            hitpoint['shape'].delete()
            hitpoint['shape2'].delete()
            i1 += 1
            print(i1)
            continue
        else:
            x, y = int(hitpoint['x'])/osu_w*WIDTH+100, int(hitpoint['y'])/osu_h*HEIGHT+50
            hitpoint['shape2'] = pyglet.shapes.Circle(x, y, RADIUS*(1+(gen_time-t)/2000), batch=outer_batch)
            hitpoint['shape2'].opcatiy = 50
            hitpoint['shape'] = pyglet.shapes.Circle(x, y, RADIUS, color=(255, 255, 0), batch=circle_batch)

# pImg=None
# g_CamTex = glGetIntegerv(GL_TEXTURE_BINDING_2D)
# def camera(dt):
#     global pImg
#     # find_finger_pos()
#     frame = cap.read(0)
#     cv2.cvtColor(frame, frame, cv2.COLOR_BGR2RGB)
#     glBindTexture(GL_TEXTURE_2D, g_CamTex)
#     glTexSubImage2D(GL_TEXTURE_2D, 0,
#                     (WIDTH - frame.cols)/2,
#                     (HEIGHT - frame.rows)/2,
#                     frame.cols, frame.rows,
#                     GL_RGB, GL_UNSIGNED_BYTE, frame.data)
#     pImg = pyglet.image.ImageData(WIDTH, HEIGHT, 'BGR', g_CamTex)
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
image = cap.read()
image = image[1]
pyimg = cv2glet(image)

def find_finger_pos(dt):
    global tip, mcp, image
    with mp_hands.Hands(
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:
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
            for hand_landmarks in results.multi_hand_landmarks:
                # mp_drawing.draw_landmarks(
                #     image,
                #     hand_landmarks,
                #     mp_hands.HAND_CONNECTIONS,
                #     mp_drawing_styles.get_default_hand_landmarks_style(),
                #     mp_drawing_styles.get_default_hand_connections_style())
                tip = [hand_landmarks.landmark[8].x, hand_landmarks.landmark[8].y,hand_landmarks.landmark[8].z]
                mcp = [hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y,hand_landmarks.landmark[0].z]

def update_camera(dt):
    global pyimg
    raw_frame = image
    frame = cv2.resize(raw_frame, None, fx=2, fy=2)
    frame = cv2.flip(frame, 1)
    pyimg = cv2glet(frame)


@window.event()
def on_draw():
    window.clear()
    pyimg.blit(0,0)
    outer_batch.draw()
    circle_batch.draw()
    
bgm.play()
#pyglet.clock.schedule_interval(find_finger_pos, 1)
pyglet.clock.schedule_interval(update_camera, 1/24)
pyglet.clock.schedule_interval(update_circle, 1/100)
pyglet.app.run()