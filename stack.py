#!/usr/bin/env python

import glob, sys
import json
from PIL import Image, ImageMath, ImageOps, ImageChops, ImageFilter
from PIL.Image import blend as imageBlend

#
# Image-stacking script
# Takes a list of files to blend on the commandline
# Saves out.png at the end
#

def main():
	if len(sys.argv)<1:
		print("Come on, give me some files to play with")
		return
		
	curves=None
	try:
		rgb=json.loads(open("adjustment.json", "r").read())
		curves=rgb["red"]+rgb["blue"]+rgb["green"]
		print("Loaded curve adjustment layer")
	except:
		print("Some problem reading adjustment.json")
		pass
	
	print("Reading image " + sys.argv[1])
	img=Image.open(sys.argv[1]).convert("RGB")
	n=0
	for f in sys.argv[1:]:
		new=Image.open(f).convert("RGB")
		if curves is not None:
			new=new.point(curves)
		n+=1
		print("Read in image [%04d] [%s]" % (n,f))
		img=imageBlend(img, new, 1.0/n)
		del(new)
	
	img.convert("RGB").save("out.png")
	print("Written out.png")

if __name__=="__main__":
	main()

