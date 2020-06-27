#!/usr/bin/env python

from PIL import Image
from sys import argv
import os
import glob
import time
from os.path import getmtime
from PIL import Image, ImageOps, ImageChops, ImageFilter
from PIL.Image import blend as imageBlend

def tlog(s):
    "Output info log message S"
    print("%s: %s" % (time.asctime(), s))
