#!/usr/bin/env python

import sys
from PIL import Image, ImageDraw, ImageFont
import subprocess
import math
import getopt
import io

### constants
fps = 30
waittime = 1 # seconds
stretchtime = 1.5 # seconds
outputaspect = 16/9
background = (0, 0, 0, 0)
outputwidth = 1920
resample = Image.LANCZOS
fontmargin = int(outputwidth / 25)

pctfontname = "UbuntuMono-Regular.ttf"
pctfontsize = int(outputwidth / 10)
pctfontcolor = "yellow"

creditfontname = "BarlowCondensed-Medium.ttf"
creditfontsize = int(outputwidth / 20)
creditfontcolor = "yellow"

### get arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "i:o:m:c:pr:b:")
except getopt.GetoptError as err:
    print(err)
    sys.exit(2)

inputimage = None
outputvideo = None
mag = None
centery = None
drawpercentage = False
credit = None
for o, a in opts:
    if o == "-i":
        inputimage = a
    elif o == "-o":
        outputvideo = a
    elif o == "-m":
        mag = int(int(a)/100)
    elif o == "-c":
        centery = int(a)
    elif o == "-p":
        drawpercentage = True
    elif o == "-r":
        credit = a
    elif o == "-b":
        background = a
    else:
        assert False, "unhandled option"

if not inputimage:
    print("input image (-i) not specified")
    sys.exit(2)
if not outputvideo:
    print("output video (-o) not specified")
    sys.exit(2)
if not mag:
    print("magnification (-m) not specified")
    sys.exit(2)

# animated GIF special case
if outputvideo.endswith('.gif'):
    fps = int(fps / 3)

### computed
waitframes = int(waittime * fps)
stretchframes = int(stretchtime * fps)
outputheight = int(outputwidth / outputaspect)
pctfont = ImageFont.truetype(pctfontname, pctfontsize)
creditfont = ImageFont.truetype(creditfontname, creditfontsize)

### initial resize
orig = Image.open(inputimage)
origwidth, origheight = orig.size
origaspect = origwidth / origheight
if not centery:
    centery = math.floor(origheight / 2)

newwidth = origwidth
newheight = int(origwidth / outputaspect)
x1 = 0
y1 = int(math.floor((newheight - origheight) / 2))

if origaspect > outputaspect:
    y1 = int(math.floor((newheight - origheight) / 2))
    new = Image.new("RGBA", (newwidth, newheight), background)
    new.paste(orig, (x1, y1, x1 + origwidth, y1 + origheight))
    orig = new
    del new
    centerpct = (centery + y1) / newheight
else:
    y1 = int(math.floor((origheight - newheight) / 2))
    orig = orig.crop((x1, y1, x1 + origwidth, y1 + newheight))
    centerpct = (centery - y1) / newheight

yoffsetbegin = (.5 - centerpct) * outputheight
yoffsetend = 0

### defs
def ease(t):
    # return t
    e = 3
    t = t * 2
    if t <= 1:
        return math.pow(t, e) / 2
    else:
        return (2 - math.pow(2 - t, e)) / 2

def process(t):
    curmag = 1 + ease(t)*(mag - 1)
    height = int(outputheight*curmag)
    copy = orig.resize((outputwidth, height), resample)
    yc = int(height * centerpct)
    yoffset = yoffsetbegin + ease(t) * (yoffsetend - yoffsetbegin)
    x1 = 0
    y1 = yc - int(outputheight/2) + yoffset
    x2 = outputwidth
    y2 = y1+outputheight
    if y1 < 0:
        y1 = 0
        y2 = outputheight
    elif y2 > height:
        y1 = height-outputheight
        y2 = height
    copy = copy.crop((x1, y1, x2, y2))
    if drawpercentage:
        msg = str(int(curmag*100)) + "%"
        draw = ImageDraw.Draw(copy)
        tw, th = pctfont.getsize(msg)
        draw.text((outputwidth-tw-fontmargin, outputheight-th-fontmargin), msg, font=pctfont, fill=pctfontcolor)
    if credit:
        msg = credit
        draw = ImageDraw.Draw(copy)
        tw, th = creditfont.getsize(msg)
        draw.text((fontmargin, outputheight-th-fontmargin), msg, font=creditfont, fill=creditfontcolor)
    return copy

def wait(copy, frames):
    output = io.BytesIO()
    copy.save(output, "PNG")
    data = output.getvalue()
    del output
    for i in range(0, frames):
        pipe.stdin.write(data)

### special case for still image output
if outputvideo.endswith('.jpg') or outputvideo.endswith('.png'):
    copy = process(1)
    if outputvideo.endswith('.jpg'):
        copy.save(outputvideo, "JPEG")
    elif outputvideo.endswith('.png'):
        copy.save(outputvideo, "PNG")
    sys.exit()

### setup pipes
# https://stackoverflow.com/questions/43650860/pipe-pil-images-to-ffmpeg-stdin-python
cmd = [
    'ffmpeg',
    '-y',
    '-f', 'image2pipe',
    '-vcodec', 'png',
    '-r', str(fps),
    '-i', '-',
]

if outputvideo.endswith('.mkv'):
    cmd = cmd + [
        '-vcodec', 'ffv1',
        '-level', '3',
        '-threads', '8',
        '-coder', '1',
        '-context', '1',
        '-g', '1',
        '-slices', '24',
        '-slicecrc', '1',
        '-pix_fmt', 'yuva444p'
    ]

if outputvideo.endswith('.mp4'):
    cmd = cmd + [
        '-pix_fmt', 'yuv420p'
    ]

cmd = cmd + [
    '-r', str(fps),
    outputvideo
]

pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)

### show original image for waittime
copy = process(0)
wait(copy, waitframes)

### stretch to mag
for i in range(0, stretchframes+1):
    t = i/(stretchframes)
    copy = process(t)
    copy.save(pipe.stdin, "PNG")

### wait
wait(copy, waitframes-1)

### unstretch
for i in range(stretchframes, 0, -1):
    t = i/(stretchframes)
    copy = process(t)
    copy.save(pipe.stdin, "PNG")

### wait
wait(copy, waitframes)

### cleanup
pipe.stdin.close()
pipe.wait()

if pipe.returncode != 0:
    raise subprocess.CalledProcessError(pipe.returncode, cmd)