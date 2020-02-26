# vmaganimate.py

Create an animated vertical magnification for a better visualization of the
process. Intended for flat Earth debunking.

For more background information, please read https://www.metabunk.org/threads/how-to-take-a-photo-of-the-curve-of-the-horizon.8859/

Requirements:

* Python 3
* ffmpeg in path
* PIL (`pip install PIL`)

Usage:

```
./vmaganimate.py -i inputimage.png -o outputvideo.mp4 -m 2000 -c 1200 \
    [-p] [-r 'credit text'] [-b "#ffffff"]
```

Mandatory parameters:

* -i: the input image, supports all the formats supported by PIL
* -o: the output image, can be mp4, mkv, gif or png. mkv output will give
a huge uncompressed output with alpha.
* -m: the amount of magnification in percent
* -c: the vertical center of the image in pixels.

Optional parameters:

* -p: show magnification percentage indicator
* -r: show the specified credit text
* -b: the background color of the results, only visible if the image is
smaller than the frame.