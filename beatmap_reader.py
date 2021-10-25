# Modified from: https://gist.github.com/marios8543/71e559f575b72088eaf0cc6495bfa483

def blank(line):
    if line=='' or line=='/n':
        return 1

def get_line(osu, phrase):
    for num, line in enumerate(osu, 0):
        if phrase in line:
            return num

def read_beatmap(filename):
    osu = open(filename,'r+').readlines()
    hitobjects = []

    hit_line = get_line(osu, '[HitObjects]')
    hitobject_list = osu[hit_line:]
    i=1
    for item in hitobject_list:
        if ',' in item:
            item = item.split(',')
            point = {
                'x':item[0],
                'y':item[1],
                'time':item[2],
                'finish':item[4],
            }
            point['num'] = str(i)
            if point['finish'] != '0':
                i = 1
            else:
                i += 1
            hitobjects.append(point)
    return hitobjects