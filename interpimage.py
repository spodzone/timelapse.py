#!/usr/bin/env python

#
# Class for an image to be interpolated
# includes useful methods to manipulate images on the way out
#

import time
from os.path import getmtime
import Image
import ImageOps
import ImageChops
import ImageFilter
from Image import blend as imageBlend
from PIL.ExifTags import TAGS


def lookupDef(hash, v, d=0):
    "Dict lookup with default value (0)"
    try:
        return hash[v]
    except KeyError:
        return d


class InterpImage(object):

    def __init__(self, fname, t=None, gamma=None, mask=None, blur=0, ac=0.0,
                 crop=None, scale=None, rotate=None, curves=None):
        self.img = None
        self.filename = fname
        if t is not None:
            self.ctime = t
        self.gamma = gamma
        self.mask = mask
        self.blur = blur
        self.ac = ac
        self.crop = crop
        self.scale = scale
        self.rotate = rotate
        self.curves = curves
        self.image = self.loadImage()

    def loadImage(self):
        self.img = Image.open(self.filename).convert("RGB")
        if self.curves is not None:
            self.img = self.img.point(self.curves)
        if self.rotate is not None:
            self.img = self.img.rotate(self.rotate, Image.BILINEAR, True)
        if self.crop is not None:
            print "crop %s" % self.crop
            self.img = self.img.crop(tuple(self.crop[0] + self.crop[1]))
            self.img.load()
        if self.scale is not None:
            self.img = self.img.resize(tuple(self.scale), Image.ANTIALIAS)

        return self.img

    def get_exif(self):
        "Return a hash of EXIF info for the current image"
        ret = {}
        i = Image.open(self.filename)
        info = i._getexif()
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            ret[decoded] = value
        self.exif = ret
        return self.exif

    def isoTime(self, t):
        "Convert a time to ISO format"
        return time.strftime("%Y-%m-%dT%H:%M:%S", t)

    def imageCtime(self):
        "Return either the EXIF image-creation date if possible or file mtime"
        try:
            exif = self.get_exif()
            timestr = lookupDef(exif, "DateTimeOriginal",
                                lookupDef(exif, "DateTime",
                                          lookupDef(exif, "DateTimeDigitized",
                                                    getmtime(self.filename))))
        except:
            timestr = getmtime(self.filename)

        try:
            if type(timestr) == float:
                ret = timestr
            else:
                ret = time.mktime(time.strptime(timestr, "%Y:%m:%d %H:%M:%S"))
        except ValueError:
            if type(timestr) == float:
                ret = timestr
            else:
                ret = time.mktime(time.strptime(timestr, "%Y-%m-%dT%H:%M:%S"))
        self.ctime = ret
        return self.ctime

    def interp(self, other, r):
        "Interpolate r proportion of the way between this and another image"
        try:
            print "image %s" % self.image
            print "other %s" % other
            print "rem %s" % r
            ret = imageBlend(self.image, other.image, r).convert("RGB")
        except ValueError:
            print ("Eeeek! Failed to blend %s and %s" %
                   (self.filename, other.filename))
            ret = None
            pass
        return ret

    def reap(self):
        "unload image from memory"
        try:
            if self.img is not None:
                del(self.img)
        except AttributeError:
            pass

    def __str__(self):
        "Return a string representation of self S"
        return ("  Filename: [%s]\n  Gamma: [%s]\n  Time: [%s]\n" %
                (self.filename, str(self.gamma), str(self.imageCtime())))

    def __repr__(self):
        "Return a string representation of self S"
        return ("  Filename: [%s]\n  Gamma: [%s]\n  Time: [%s]\n" %
                (self.filename, str(self.gamma), str(self.imageCtime())))


def imageGamma(img, g=(1.0, 1.0, 1.0), depth=256):
    "Apply a gamma curve to image"
    ret = img
    if g != (1.0, 1.0, 1.0):
        (rg, gg, bg) = g
        rtable = map(lambda x: int(depth * (float(x) / depth) ** (1.0 / rg)),
                     range(depth))
        gtable = map(lambda x: int(depth * (float(x) / depth) ** (1.0 / gg)),
                     range(depth))
        btable = map(lambda x: int(depth * (float(x) / depth) ** (1.0 / bg)),
                     range(depth))
        table = rtable + gtable + btable
        ret = img.point(table)
    return ret


def imageMask(img, mask):
    if mask is not None:
        return ImageChops.multiply(img, mask)
    else:
        return img


def imageBlur(img, degree):
    if degree == 0.0:
        return img
    else:
        for i in range(int(degree)):
            img = img.filter(ImageFilter.BLUR)
        b = img
        b = b.filter(ImageFilter.BLUR)
    return imageBlend(img, b, float(degree - int(degree)))


def imageAutoContrast(img, r=1.0):
    "Return a blend of image IMG with its auto-contrasted self"
    if r == 0.0:
        return img
    ac = ImageOps.autocontrast(img)
    return imageBlend(img, ac, r)
