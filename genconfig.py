#!/usr/bin/env python

#
# Generate a JSON config for interpolation library
#
# Usage:
#
#   ./genconfig.py 'in/*.jpg' 100 'out/' > cfg.json 
#

import json, sys, os, glob
from interpimage import *

def main():
	pattern=""
	if len(sys.argv)>1:
		pattern=sys.argv[1]
	
	noframes=100	
	if len(sys.argv)>2:
		noframes=int(sys.argv[2])
		
	outdir="out/"
	if len(sys.argv)>3:
		outdir=sys.argv[3]
		
	filelist=glob.glob(pattern)
	
	ims=sorted([ InterpImage(f) for f in filelist ], key=lambda x: x.imageCtime())
	
	data={
	"filelist": [ {"name": f.filename, "time": f.imageCtime()} for f in ims ],
	"inpattern": 	pattern,
	"outdir": 		outdir,
	"outformat": 	"png",
	"noframes": 	100,
	"gammas": 		[],
	"blur": 			[],
	"mask": 			[],
	"ac":   			[],
	"rotate":			0,
	"nothreads":	5,
	"crop":  [[], [] ],
	"scale": [  ]
	}
	
	print json.dumps(data, indent=2, sort_keys=True)

if __name__=="__main__":
	main()
