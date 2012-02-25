#!/usr/bin/env python

#
# Class for a Timeline of images and manipulations for linear interpolation
#

import sys
from os.path import getmtime
import json
import Image
import threading

from interpimage import *

class Timeline:
	
	def __init__(s, fname):
		s.config=json.loads(open(fname, "r").read())
		
		s.crop=lookupDef(s.config, "crop", None)
		s.scale=lookupDef(s.config, "scale", None)
		s.rotate=lookupDef(s.config, "rotate", None)
		s.nothreads=lookupDef(s.config, "nothreads", 5)
		
		s.curves=None
		curves=lookupDef(s.config, "curves", None)
		if curves is not None:
			rgb=json.loads(open(curves, "r").read())
			s.curves=rgb["red"]+rgb["blue"]+rgb["green"]

		s.filelist=[ InterpImage(x["name"], 
			lookupDef(x, "time", None), 
			lookupDef(x, "gamma", (1.0, 1.0, 1.0) ),
			lookupDef(x, "mask", None),
			lookupDef(x, "blur", 0),
			lookupDef(x, "ac", 0),
			s.crop,
			s.scale,
			s.rotate,
			s.curves
			) 
			for x in s.config["filelist"] ]
			
		s.filelist=sorted(s.filelist, key=lambda x: x.imageCtime())
		
		s.inpattern=s.config["inpattern"]
		s.outdir=s.config["outdir"]
		s.outformat=s.config["outformat"]
		s.noframes=s.config["noframes"]
		
		if s.outformat is None:
			s.outformat="jpg"
		
		s.gammas=[]
		s.gammas+=map(lambda i: ( i.imageCtime(), tuple(i.gamma)), s.filelist)
		try:
			s.gammas+=map(lambda i: (i[0], tuple(i[1])), s.config["gammas"])
		except KeyError:
			pass
		
		s.gammas=sorted(s.gammas, key=lambda s: s[0])
		
		s.masks=[]
		s.masks+=map(lambda i: ( i.imageCtime(), i.mask), s.filelist)
		try:
			s.masks+=map(lambda i: ( i[0], i[1]), s.config["masks"])
		except KeyError:
			pass
		
		s.masks=sorted(s.masks, key=lambda s: s[0])
		
		s.blur=[]
		s.blur+=map(lambda i: ( i.imageCtime(), i.blur), s.filelist)
		try:
			s.blur+=map(tuple, s.config["blur"])
		except KeyError:
			pass
		
		s.blur=sorted(s.blur, key=lambda s: s[0])

		s.ac=[]
		s.ac+=map(lambda i: ( i.imageCtime(), i.ac), s.filelist)
		try:
			s.ac+=map(tuple, s.config["ac"])
		except KeyError:
			pass
		
		s.ac=sorted(s.ac, key=lambda s: s[0])

	def fileTimes(s):
		return [ x.imageCtime() for x in s.filelist ]
		
	def minTime(s):
		ftimes=sorted(s.fileTimes())
		return ftimes[0]

	def maxTime(s):
		ftimes=sorted(s.fileTimes())
		return ftimes[-1]

	def filesAtTime(s, t):
		"Find nearest filename to a given time, returns index and inter-image time proportion"
		idx=0
		while (s.filelist[idx].imageCtime()<t) and idx<len(s.filelist)-1:
			idx+=1
		idx=max(0, idx-1)
		rem=t-(s.filelist[idx].imageCtime())
		diff=s.filelist[idx+1].imageCtime() - s.filelist[idx].imageCtime()
		try:
			r=float(rem)/diff
		except:
			r=0.0
		return (idx, r)

	def gammaAtTime(s, t):
		"Find gamma at given time T"
		idx=0
		while (s.gammas[idx][0]<t) and (idx<=len(s.gammas)-1):
			idx+=1
		idx-=1
		t1, t2=s.gammas[idx][0], s.gammas[idx+1][0]
		g1, g2=s.gammas[idx][1], s.gammas[idx+1][1]
		rem=float(t-t1)
		factor=float(rem)/(t2-t1)
		if type(g1)==tuple:
			rgamma=float(g1[0])+(g2[0]-g1[0])*factor
			ggamma=float(g1[1])+(g2[1]-g1[1])*factor
			bgamma=float(g1[2])+(g2[2]-g1[2])*factor
			return (rgamma, ggamma, bgamma)
		else:
			g=g1+(g2-g1)*factor
			return (g,g,g)
			
	def blurAtTime(s, t):
		"Find blur at given time T"
		idx=0
		while (s.blur[idx][0]<t) and (idx<=len(s.blur)-1):
			idx+=1
		idx-=1
		t1, t2=s.blur[idx][0], s.blur[idx+1][0]
		b1, b2=s.blur[idx][1], s.blur[idx+1][1]
		factor=float(t-t1)/(t2-t1)
		b=float(b1)+float(b2-b1)*factor
		return b
			
	def acAtTime(s, t):
		"Find auto-correction factor at given time T"
		idx=0
		while (s.ac[idx][0]<t) and (idx<=len(s.ac)-1):
			idx+=1
		if idx>0:
			idx-=1
		t1, t2=s.ac[idx][0], s.ac[idx+1][0]
		b1, b2=s.ac[idx][1], s.ac[idx+1][1]
		factor=float(t-t1)/float(t2-t1)
		b=float(b1)+float(b2-b1)*factor
		return b
			
	def maskAtTime(s, t):
		"Compute an image mask for time T"
		idx=0
		while (s.masks[idx][0]<=t) and (idx<len(s.gammas)):
			idx+=1
		if idx>0:
				idx-=1
		t1,t2=s.masks[idx][0], s.masks[idx+1][0]
		m1,m2=s.masks[idx][1], s.masks[idx+1][1]
		factor=(t-t1)/float(t2-t1)
		if m1 is not None and m2 is not None:
			a=Image.open(m1).convert("RGB")
			b=Image.open(m2).convert("RGB")
			ret=a
			try:
				ret=Image.blend(a, b, factor)
			except ValueError:
				print "Images of differing sizes: m1=(%d,%d), m2=(%d,%d)" % (a.size+b.size)
			return ret
		else:
			return None;
			
	def __str__(s):
		"Return string representation of self S"
		return "Filelist: [%s]\nGammas: [%s]\nMasks: [%s]\nBlurs: [%s]\nAutoContrasts: [%s]\nRequired number of files: [%d]\nOutput base dir: [%s]" % ("\n".join(map(repr, s.filelist)), str(s.gammas), str(s.masks), str(s.blur), str(s.ac), s.noframes, s.outdir)
		
	def frameAtTime(s, t, fname=None):
		idx,rem=s.filesAtTime(t)
		g=s.gammaAtTime(t)
		blur=s.blurAtTime(t)
		msk=s.maskAtTime(t)
		ac=s.acAtTime(t)
		print "Image t=%f, g=(%f,%f,%f), blur=%f, ac=%f, f1=%s, f2=%s" % (t, g[0],g[1],g[2], blur, ac, s.filelist[idx].filename, s.filelist[idx+1].filename)
		result=s.filelist[idx].interp(s.filelist[idx+1], rem)
		result=imageAutoContrast(result, ac)
		result=imageMask(result, msk)
		result=imageGamma(result, g)
		result=imageBlur(result, blur)
		if fname is not None:
			result.save(fname)
		return result

	def renderLinear(s, nframes=None):
		if nframes:
			s.noframes=nframes
		mint=s.minTime()
		maxt=s.maxTime()
		for n in range(s.noframes):
			t=float(n)/s.noframes*(maxt-mint)+mint
			result=s.frameAtTime(t)
			result.save("%s/result-%05d.%s" % (s.outdir, n, s.outformat))
			[ i.reap() for i in s.filelist ]
			
	def renderThreads(s, nthreads=5):
		mint=s.minTime()
		maxt=s.maxTime()
		threads=[]
		n=0
		while n<s.noframes:
			t=float(n)/s.noframes*(maxt-mint)+mint
			idx,rem=s.filesAtTime(t)
			threads.append(threading.Thread(target=s.frameAtTime, args=(t, "%s/result-%05d.%s" % (s.outdir, n, s.outformat) ) ) )
			if len(threads)==nthreads:
				[ t.start() for t in threads ]
				[ t.join()  for t in threads ]
				if idx>5:
					[ i.reap() for i in s.filelist[:idx-2] ]
				threads=[]
			n+=1
		print "Tidying up"
		[ t.start() for t in threads ]
		[ t.join()  for t in threads ]
			
	def render(s):
		print "Rendering with %d threads" % s.nothreads
		if s.nothreads==1:
			s.renderLinear()
		else:
			s.renderThreads(nthreads=s.nothreads)
			
def test(s):
		pass

def test():
	conffile="test-config.json"
	tl=Timeline(conffile)
	print "Timeline found:\n" + str(tl)
	tl.render()

if __name__=="__main__":
	test()

