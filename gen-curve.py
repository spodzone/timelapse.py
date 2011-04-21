#!/usr/bin/env python

#
# Assist generating custom curve mappings
#
#
# Usage: 
# ./gen-curve.py     
#	 					with no parameters will output greyscale-strip.png
#						At this point, you go edit it in Photoshop or Gimp etc
# ./gen-curve.py greyscale-strip.png
#						with filename, will assume leftmost pixel=0, rightmost=255
#						and generate curves accordingly
#

import Image
import json
from sys import argv


def generate(fname="greyscale-strip.png"):
	#write a greyscale spectrum to file fname, for editing in gimp/etc
	img=Image.new("RGB", (256,10) )
	print "New image size: %s" % str(img.size)
	for y in range(10):
		for x in xrange(256):
			img.putpixel( (x,y), (x,x,x) )
	img.save(fname)

def readBack(fname="greyscale-strip.png"):
	#read file fname and generate curves as JSON config files
	img=Image.open(fname).convert("RGB")
	r=[]
	g=[]
	b=[]
	ps=[]
	for x in xrange(256):
		px=img.getpixel ( (x,1) )
		r.append(px[0])
		g.append(px[1])
		b.append(px[2])
		ps.append(px)
	data={
	"red": r,
	"green": g,
	"blue": b
	}
	print json.dumps(data, indent=2, sort_keys=False)


if __name__=="__main__":
	if len(argv)>1:
		readBack(argv[1])
	else:
		generate()
