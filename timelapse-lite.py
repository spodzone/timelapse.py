#!/usr/bin/env python

from PIL import Image
import sys
import os
import glob
import time
from os.path import getmtime
from PIL import Image, ImageOps, ImageChops, ImageFilter
from PIL.Image import blend as imageBlend
from multiprocessing.dummy import Pool as ThreadPool


def tlog(s):
    "Output info log message S"
    print("%s: %s" % (time.asctime(), s))

def pMap(fn, arr, threads=2):
    pool = ThreadPool(threads)
    results = pool.map(fn, arr)
    pool.close()
    pool.join()
    return results


def findFiles(indir):
    "return sorted list of input files and mtimes"
    fnames = glob.glob(indir + "/*")
    mtimes=map(getmtime, fnames)
    filedata=sorted(zip(mtimes, fnames))
    return filedata


def filebefore(filedata, ts):
    "return last filename before ts"
    return [ (fts,fname) for (fts,fname) in filedata if fts<=ts ][-1]

def fileafter(filedata, ts):
    "return first filename after ts"
    return [ (fts,fname) for (fts,fname) in filedata if fts>=ts ][0]

def tsproportion(filedata, ts):
    "return proportion ts falls between two image timestamps"
    leftimg=filebefore(filedata, ts)[0]
    rightimg=fileafter(filedata, ts)[0]
    if(leftimg==rightimg):
        prop=0
    else:
        prop=(ts-leftimg)/(rightimg-leftimg)
    return prop

def mktasks(filedata, noframes):
    "convert file data to list of interpolation tasks"
    mints, maxts=(filedata[0][0], filedata[-1][0])
    timestamps=[ mints+(maxts-mints)*i/noframes for i in range(noframes) ]
    filebefores=[ filebefore(filedata, ts)[1] for ts in timestamps ]
    fileafters=[ fileafter(filedata, ts)[1] for ts in timestamps ]
    tasks=[ tsproportion(filedata, ts) for ts in timestamps ]
    return list(zip(filebefores, fileafters, tasks, range(noframes)))


def interpolateImage(task, outdir):
    "implement task - interpolate between two images"
    f1,f2,alpha,counter=task
    tlog("Image %d: files=[%s],[%s] prop=%f" % ( counter,f1,f2,alpha))
    img1=Image.open(f1).convert("RGB")
    img2=Image.open(f2).convert("RGB")
    img=imageBlend(img1, img2, alpha).convert("RGB")
    outfname=outdir+"/img-%05d.jpg" % (counter)
    img.save(outfname)

def interpolateImages(tasks, outdir, threads=2):
    "main loop - run a list of tasks"
    pMap(lambda t: interpolateImage(t, outdir), tasks, threads)


def main():
    (noframes, indir, outdir, threads) = [1500, "jpeg-in", "jpeg-out", 2]
    tlog("Parameters")
    if len(sys.argv) > 1:
        noframes = int(sys.argv[1])
    if len(sys.argv) > 2:
        indir = sys.argv[2]
    if len(sys.argv) > 3:
        outdir = sys.argv[3]
    if len(sys.argv) > 4:
        threads = int(sys.argv[4])

    tlog("Finding files")
    filedata=findFiles(indir)

    tlog("Building task-list")
    tasks=mktasks(filedata, noframes)

    tlog("Running")
    interpolateImages(tasks, outdir, threads)

if __name__ == "__main__":
    main()
