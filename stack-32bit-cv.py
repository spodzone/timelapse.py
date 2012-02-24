#!/usr/bin/env python

import glob, sys, cv, json, OpenEXR, Imath

#
# Image-stacking script
# Takes a list of files to blend on the commandline
# Saves out.png at the end
#

def imageBlend(a, b, r):
	img = cv.CreateImage(cv.GetSize(a), cv.IPL_DEPTH_32F, 3)
	cv.AddWeighted(a, 1.-r, b, r, 0, img)
	return img


def main():
	if len(sys.argv)<1:
		print "Come on, give me some files to play with"
		return
		
	print "Reading image " + sys.argv[1]
	
	incoming=cv.LoadImageM(sys.argv[1])
	w,h=(incoming.cols,incoming.rows)
	nw,nh=(int(w*1.5+0.5), int(h*1.5+0.5))
	img = cv.CreateImage(cv.GetSize(incoming), cv.IPL_DEPTH_32F, 3)
	cv.Convert(incoming, img)

	n=0
	for f in sys.argv[1:]:
		incoming=cv.LoadImageM(f)
		w,h=(incoming.cols, incoming.rows)
		nw,nh=(int(w*1.5+0.5), int(h*1.5+0.5))
		new = cv.CreateImage(cv.GetSize(incoming), cv.IPL_DEPTH_32F, 3)
		cv.Convert(incoming, new)

		n+=1
		print "Read in image [%04d] [%s]" % (n,f)
		img=imageBlend(img, new, 1.0/n)
		
		del(new)
		
	out=cv.CreateImage(cv.GetSize(img), cv.IPL_DEPTH_16U, 3)
	cv.ConvertScale(img, out, 256.)
	cv.SaveImage("out-16-up.png", out)
	print "Written out-16-up.png"

if __name__=="__main__":
	main()

