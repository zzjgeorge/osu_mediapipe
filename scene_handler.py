from beatmap_reader import *
import pyglet
import time

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

@window.event()
def on_draw():
    window.clear()
    outer_batch.draw()
    circle_batch.draw()
    
bgm.play()
pyglet.clock.schedule_interval(update_circle, 1/100)
pyglet.app.run()