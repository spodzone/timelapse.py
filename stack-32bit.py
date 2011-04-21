#!/usr/bin/env python

import glob, sys
import json
import Image, ImageMath, ImageOps, ImageChops, ImageFilter
#from Image import blend as imageBlend

#
# Image-stacking script
# Takes a list of files to blend on the commandline
# Saves out.png at the end
#

def imageBlend(a, b, r):
	return ImageMath.eval("a+(b-a)*r", a=a,b=b,r=r)


def main():
	if len(sys.argv)<1:
		print "Come on, give me some files to play with"
		return

	curves=None
	try:
		rgb=json.loads(open("adjustment.json", "r").read())
		curves=rgb["red"]+rgb["blue"]+rgb["green"]
		print "Loaded curve adjustment layer"
	except:
		print "Some problem reading adjustment.json"
		pass
		
	print "Reading image " + sys.argv[1]
	img=Image.open(sys.argv[1]).convert("RGB")
	if curves is not None:
		img=img.point(curves)

	imgr,imgg,imgb=[ r.convert("F") for r in img.split() ]
	n=0

	for f in sys.argv[1:]:
		new=Image.open(f).convert("RGB")
		if curves is not None:
			new=new.point(curves)

		newr,newg,newb=[ r.convert("F") for r in new.split() ]
		
		n+=1
		print "Read in image [%04d] [%s]" % (n,f)
		imgr=imageBlend(imgr, newr, 1.0/n)
		imgg=imageBlend(imgg, newg, 1.0/n)
		imgb=imageBlend(imgb, newb, 1.0/n)
		del(new)
		del(newr)
		del(newg)
		del(newb)
	
	imgr.convert("RGB").save("out-r32.png")
	imgg.convert("RGB").save("out-g32.png")
	imgb.convert("RGB").save("out-b32.png")

	img=Image.merge("RGB", [ b.convert("L") for b in (imgr,imgg,imgb) ]).convert("RGB")
	img.convert("RGB").save("out32.png")
	print "Written out.png"

if __name__=="__main__":
	main()

