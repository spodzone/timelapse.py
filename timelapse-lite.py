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


def findFiles(indir):
    "return sorted list of input files and mtimes"
    fnames = glob.glob(indir + "/*")
    mtimes=map(getmtime, fnames)
    filedata=sorted(zip(mtimes, fnames))
    return filedata

def main():
    (noframes, indir, outdir) = [1500, "jpeg-in", "jpeg-out"]
    if len(sys.argv) > 1:
        noframes = sys.argv[1]
    if len(sys.argv) > 2:
        indir = sys.argv[2]
    if len(sys.argv) > 3:
        outdir = sys.argv[3]


if __name__ == "__main__":
    main()
