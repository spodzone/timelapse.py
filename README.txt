timelapse.py
============

Linear image interpolation for timelapse video (amongst other things)

Copyright (C) Tim Haynes  <timelapse@stirfried.vegetable.org.uk> 2010


What?
====

When making a timelapse video, it is often assumed that you will shoot enough
source images, at uniform intervals, to be able to make a movie at 25fps.
Furthermore, it is assumed that these images are the right shape and size, free
from defect, with the desired lighting colours. 

In practice, the lighting frequently changes, the camera exposure and 
whitebalance might change, the battery needs changed, .. there are number of 
factors that detract for the ideal.

Timelapse.py has no such assumptions. Given a number of source images, it will
generate replacement intermediate frames at regular intervals. The configuration
file (in human-friendly JSON format) allows you to assign a number of effects, 
either aligned with specific  input files, or by time.

As such, it may also be used for creating shorter film snippets, such as 
cross-fade, fade-in or fade-out, blurring and vignetting.


Dependencies
============

timelapse.py has a primary requirement of Python 2.6 and the Python Image 
Library (PIL). It has been tested with python 2.6.4 and 2.6.5 on Debian 
GNU/Linux ("squeeze") and Mac OS X (Snow Leopard). Hopefully it should work
on other platforms, but python 3.x has not been tested yet.


File Formats
============

PIL supports many file formats, most notably JPEG (jpg), PNG, TIFF, BMP and 
more. Any combination may be used for input, and one format chosen for output.
A particular favourite, for lossless compression, is to output PNG.


Effects
=======

Timelapse.py understands several different effects:


Time
----

The time at which an input file image applies may be specified explicitly in the
configuration file, or if omitted, the script will attempt to use the original
creation time from EXIF information in the image; failing that, the file's
modification time on disk will be used.

The units may be thought of as nominal seconds. When working from EXIF and file
mtime, large numbers of seconds since the epoch (1970-01-01) are used. When
specifying your own time, it might be easier to start from 0 and work upwards. 
Either way, it does not matter much; the script simply takes the start and end
times and divides it into an evenly distributed number of frames.

gamma
-----

Gamma is used to control the relative brightness of either the whole image, or
to manipulate the red/green/blue channels individually. As such, a triple 
[R,G,B] is expected. The default, for no adjustment, is [1, 1, 1]; an image with
gamma [1, 1.5, 1] may be regarded as very green.

mask
----

A mask is an auxilliary input image with which the current frame is multiplied.
It may be used to add spatial manipulations, such as a classic vignette
effect (darkened corners), localized contrast (e.g. simulating a graduated 
neutral-density filter) or other tints.

blur
----

This is self-explanatory; either applied to a particular image, or at a 
particular time, the output frame(s) will be blurred.

The Python Image Library only has one blur function with no control of 
strength or degree, so the scalability has been implemented by repeating the
blur several times over (and interpolating an appropriate proportion between
blurred images so smoother continuous strengths can be supplied). A blur of 5 
is enough for a frame to appear significantly out of focus.

Unfortunately, while the rest of PIL is impressively fast, the blur operator
is particularly slow. Use with caution.

Auto-Contrast Correction
------------------------

PIL has a function for automatically normalizing an image's contrast better to
span the full range from dark shadows to bright highlights. The degree is a 
floating-point number nominally between 0 and 1.0, the extent to which the 
effect is applied.

Crop and Scale
--------------

These options may only be applied globally; first crop is applied to extract
a box from the source image, and then it is scaled down to the desired output
resolution. For example, you can take JPEG images from a dSLR and crop a 1080p 
(1920 x 1080 pixels) box out.

Interpolating Effects
---------------------

With the exception of crop and scale, all the other filters may be specified 
either tied to a particular input file, or in the global options section of
the config file, associated with a given time.

The script works by building a timeline for the list of files and for each 
effect. The interval between least and greatest time is split into a given
number of frames, and then for each required output frame, the corresponding
time is calculated. If this time falls between two input files (more likely 
than not), they will be interpolated in proportion. Similarly, each effect 
requested is interpolated: each red, green and blue parameter of the gamma 
triple is treated  separately; the degrees to which blur or auto-contrast 
normalization or an image-mask should apply are also interpolated.

All of these effects require the Image.blend() method in PIL; as such, you
*must* ensure that masks are all the same size as the input images (after taking
crop+size options into account).

  
Aside: Threading
----------------

The process of loading, computing and saving many images is quite dependent on
i/o speed. Time spent saving an output image to disk could well be spent with
the CPU calculating the next image.

As such, a crude thread-pool has been implemented (governed by the `nothreads'
global parameter) whereby the given number of threads are allocated, all
given a task of rendering a given output frame by time, and then when all are 
completed, the next batch of threads are created.

This does introduce a significant speedup - around 25% in one simple test.


How?
====

The first thing to write is a JSON configuration file. This should have a 
section `filelist' consisting of an array of hash/dict objects, each of which
gives the file `name' and optionally `time', very-optionally `blur' and `gamma'
and `ac' (auto-contrast) and `mask'.

To make the process easier, a script, genconfig.py, has been provided. It takes
a simple glob pattern as its first and only argument, and prints a JSON file
to use as a starting-point.

  bash$ ./genconfig.py 'in/*.jpg' > my_movie.json
  
This configuration file may be edited by hand in your text-editor of choice. 

To mix the sequence down, run

  bash$ ./timelapse.py my_movie.json
  
Conventionally, it makes sense to have the input files in an in/ subdirectory
and results written to a large number of PNG images in out/.

These output PNG images may be combined into a Flash, MPEG or AVI movie using 
ffmpeg(1):

  bash$ ffmpeg -f image2 -i out/result-%05d.png -sameq -y out/movie.flv
  
...and viewed using mplayer(1):

  bash$ mplayer -pp 6 out/movie.flv
  

Examples
========

Two examples are provided, using a representative set of the available filters.

First, test-blur.json fades from bright white to an image of a flower with a 
blur factor of 5. This then sharpens, bringing the image into focus; then the
contrast is increased beyond the automatically determined correct extent 
(increasing the contrast between foreground and background) and a slight green 
tint added towards the end.

The test-mask.json configuration varies the gamma tint and mask over time,
whilst keeping the basic image the same. The config file states the two files
at times t=0 and t=2 seconds; the masks (one plain white which has no effect,
one a vignette) are applied to the extremities of the timeline (one attached
to the file, one in the global section), with the vignette applied 1.5s into the
sequence. There are additional gamma triples listed which will apply at their
prescribed times through the timeline. First it turns green, then it turns
blue with darkened corners, then normal warm colour-balance is restored.

