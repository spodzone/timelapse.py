#!/usr/bin/env python

#
# Class for an image to be interpolated
# includes useful methods to manipulate images on the way out
#

import glob, time, sys
from os.path import getmtime
import Image, ImageMath, ImageOps, ImageChops, ImageFilter
from Image import blend as imageBlend
from PIL.ExifTags import TAGS

def lookupDef(hash,v,d=0):
	"Dict lookup with default value (0)"
	try:
		return hash[v]
	except KeyError:
		return d

class InterpImage:
	
	def __init__(s, fname, t=None, gamma=None, mask=None, blur=0, ac=0.0, crop=None, scale=None):
		s.filename=fname
		s.image=s.loadImage
		if t is not None:
			s.ctime=t
		s.gamma=gamma
		s.mask=mask
		s.blur=blur
		s.ac=ac
		s.crop=crop
		s.scale=scale
		
	def loadImage(s):
		try:
			if s.img is not None:
				return s.img
		except:
			s.img=Image.open(s.filename).convert("RGB")
			if s.crop is not None:
				s.img=s.img.crop( tuple(s.crop[0]+s.crop[1]))
			if s.scale is not None:
				s.img=s.img.resize( tuple(s.scale), Image.ANTIALIAS )
		return s.img
	
	def get_exif(s):
		"Return a hash of EXIF info for the current image"
		try:
			if s.exif is not None:
				return s.exif
		except:
			ret = {}
			i = Image.open(s.filename).convert("RGB")
			try:
				info = i._getexif()
				for tag, value in info.items():
					decoded = TAGS.get(tag, tag)
					ret[decoded] = value
			except:
				ret={}
			s.exif=ret
		return s.exif
	
	def isoTime(s,t):
		"Convert a time to ISO format"
		return time.strftime("%Y-%m-%dT%H:%M:%S", t)
	
	def imageCtime(s):
		"Return either the EXIF image-creation date if possible or file mtime"
		try:
			if s.ctime is not None:
				return s.ctime
		except:
			exif=s.get_exif()
			timestr=lookupDef(exif, "DateTimeOriginal", 
				lookupDef(exif, "DateTime", 
					lookupDef(exif, "DateTimeDigitized", 
						getmtime(s.filename))))
		try:
			if type(timestr)==float:
				ret=timestr
			else:
				ret=time.mktime(time.strptime(timestr, "%Y:%m:%d %H:%M:%S"))
		except ValueError:
			if type(timestr)==float:
				ret=timestr
			else:
				ret=time.mktime(time.strptime(timestr, "%Y-%m-%dT%H:%M:%S"))
		s.ctime=ret
		return s.ctime
		
	def interp(s, other, r):
		"Interpolate r proportion of the way between this and another image"
		try:
			ret=imageBlend(s.image(), other.image(), r).convert("RGB")
		except ValueError:
			print "Eeeek! Failed to blend %s and %s" % (s.filename, other.filename)
			ret=None
			pass
		return ret
		
	def reap(s):
		"unload image from memory"
		try:
			if s.img is not None:
				del(s.img)
		except AttributeError:
			pass

	def __str__(s):
		"Return a string representation of self S"
		return "  Filename: [%s]\n  Gamma: [%s]\n  Time: [%s]\n" % (s.filename, 
			str(s.gamma), 
			str(s.imageCtime()))

	def __repr__(s):
		"Return a string representation of self S"
		return "  Filename: [%s]\n  Gamma: [%s]\n  Time: [%s]\n" % (s.filename, 
			str(s.gamma), 
			str(s.imageCtime()))
		

def imageGamma(img, g=(1.0,1.0,1.0), depth=256):
	"Apply a gamma curve to image"
	ret=img
	if g!=(1.0,1.0,1.0):
		(rg,gg,bg)=g
		rtable=map(lambda x: int(depth* (float(x)/depth)**(1.0/rg)), range(depth))
		gtable=map(lambda x: int(depth* (float(x)/depth)**(1.0/gg)), range(depth))
		btable=map(lambda x: int(depth* (float(x)/depth)**(1.0/bg)), range(depth))
		table=rtable+gtable+btable
		ret=img.point(table)
	return ret
	
def imageMask(img, mask):
	if mask is not None:
		return ImageChops.multiply(img, mask)
	else:
		return img

def imageBlur(img, degree):
	for i in range(int(degree)):
		img=img.filter(ImageFilter.BLUR)
	b=img
	b=b.filter(ImageFilter.BLUR)
	return imageBlend(img, b, float(degree-int(degree)))

def imageAutoContrast(img, r=1.0):
	"Return a blend of image IMG with its auto-contrasted self"
	if r==0.0:
		return img
	ac=ImageOps.autocontrast(img)
	return imageBlend(img, ac, r)

