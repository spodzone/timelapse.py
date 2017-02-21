#!/usr/bin/env python

#
# Class for a Timeline of images and manipulations for linear interpolation
#

import json
from PIL import Image
import threading

from interpimage import *


class Timeline(object):

    def __init__(self, fname):
        self.config = json.loads(open(fname, "r").read())

        self.crop = lookupDef(self.config, "crop", None)
        if self.crop is not None:
            if len(self.crop[0]) == 0:
                self.crop = None

        self.scale = lookupDef(self.config, "scale", None)
        if self.scale is not None:
            if len(self.scale) == 0:
                self.scale = None
        self.rotate = lookupDef(self.config, "rotate", None)
        self.nothreads = lookupDef(self.config, "nothreads", 5)

        self.curves = None
        curves = lookupDef(self.config, "curves", None)
        if curves is not None:
            rgb = json.loads(open(curves, "r").read())
            self.curves = rgb["red"] + rgb["blue"] + rgb["green"]

        self.filelist = [InterpImage(x["name"], lookupDef(x, "time", None),
                                     lookupDef(x, "gamma", (1.0, 1.0, 1.0)),
                                     lookupDef(x, "mask", None),
                                     lookupDef(x, "blur", 0),
                                     lookupDef(x, "ac", 0),
                                     self.crop, self.scale,
                                     self.rotate, self.curves)
                         for x in self.config["filelist"]]

        self.filelist = sorted(self.filelist, key=lambda x: x.imageCtime())

        self.inpattern = self.config["inpattern"]
        self.outdir = self.config["outdir"]
        self.outformat = self.config["outformat"]
        self.noframes = self.config["noframes"]

        if self.outformat is None:
            self.outformat = "jpg"

        self.gammas = []
        self.gammas += map(lambda i: (i.imageCtime(), tuple(i.gamma)),
                           self.filelist)
        try:
            self.gammas += map(lambda i: (i[0], tuple(i[1])),
                               self.config["gammas"])
        except KeyError:
            pass

        self.gammas = sorted(self.gammas, key=lambda s: s[0])

        self.masks = []
        self.masks += map(lambda i: (i.imageCtime(), i.mask), self.filelist)
        try:
            self.masks += map(lambda i: (i[0], i[1]), self.config["masks"])
        except KeyError:
            pass

        self.masks = sorted(self.masks, key=lambda s: s[0])

        self.blur = []
        self.blur += map(lambda i: (i.imageCtime(), i.blur), self.filelist)
        try:
            self.blur += map(tuple, self.config["blur"])
        except KeyError:
            pass

        self.blur = sorted(self.blur, key=lambda s: s[0])

        self.ac = []
        self.ac += map(lambda i: (i.imageCtime(), i.ac), self.filelist)
        try:
            self.ac += map(tuple, self.config["ac"])
        except KeyError:
            pass

        self.ac = sorted(self.ac, key=lambda s: s[0])

    def fileTimes(self):
        return [x.imageCtime() for x in self.filelist]

    def minTime(self):
        ftimes = sorted(self.fileTimes())
        return ftimes[0]

    def maxTime(self):
        ftimes = sorted(self.fileTimes())
        return ftimes[-1]

    def filesAtTime(self, t):
        """Find nearest filename to a given time, returns index and inter-image
           time proportion

        """
        idx = 0
        while ((self.filelist[idx].imageCtime() < t) and
               idx < len(self.filelist) - 1):
            idx += 1
        idx = max(0, idx - 1)
        rem = t - (self.filelist[idx].imageCtime())
        diff = (self.filelist[idx + 1].imageCtime() -
                self.filelist[idx].imageCtime())
        try:
            r = float(rem) / diff
        except:
            r = 0.0
        return (idx, r)

    def gammaAtTime(self, t):
        "Find gamma at given time T"
        idx = 0
        while (self.gammas[idx][0] < t) and (idx <= len(self.gammas) - 1):
            idx += 1
        idx -= 1
        t1, t2 = self.gammas[idx][0], self.gammas[idx + 1][0]
        g1, g2 = self.gammas[idx][1], self.gammas[idx + 1][1]
        rem = float(t - t1)
        factor = float(rem) / (t2 - t1)
        if type(g1) == tuple:
            rgamma = float(g1[0]) + (g2[0] - g1[0]) * factor
            ggamma = float(g1[1]) + (g2[1] - g1[1]) * factor
            bgamma = float(g1[2]) + (g2[2] - g1[2]) * factor
            return (rgamma, ggamma, bgamma)
        else:
            g = g1 + (g2 - g1) * factor
            return (g, g, g)

    def blurAtTime(self, t):
        "Find blur at given time T"
        idx = 0
        while (self.blur[idx][0] < t) and (idx <= len(self.blur) - 1):
            idx += 1
        idx -= 1
        t1, t2 = self.blur[idx][0], self.blur[idx + 1][0]
        b1, b2 = self.blur[idx][1], self.blur[idx + 1][1]
        factor = float(t - t1) / (t2 - t1)
        b = float(b1) + float(b2 - b1) * factor
        return b

    def acAtTime(self, t):
        """Find auto-correction factor at given time T"""
        idx = 0
        while (self.ac[idx][0] < t) and (idx <= len(self.ac) - 1):
            idx += 1
        if idx > 0:
            idx -= 1
        t1, t2 = self.ac[idx][0], self.ac[idx + 1][0]
        b1, b2 = self.ac[idx][1], self.ac[idx + 1][1]
        factor = float(t - t1) / float(t2 - t1)
        b = float(b1) + float(b2 - b1) * factor
        return b

    def maskAtTime(self, t):
        """Compute an image mask for time T"""
        idx = 0
        while (self.masks[idx][0] <= t) and (idx < len(self.gammas)):
            idx += 1
        if idx > 0:
                idx -= 1
        t1, t2 = self.masks[idx][0], self.masks[idx + 1][0]
        m1, m2 = self.masks[idx][1], self.masks[idx + 1][1]
        factor = (t - t1) / float(t2 - t1)
        if m1 is not None and m2 is not None:
            a = Image.open(m1).convert("RGB")
            b = Image.open(m2).convert("RGB")
            ret = a
            try:
                ret = Image.blend(a, b, factor)
            except ValueError:
                print("Images of differing sizes: m1=(%d,%d), m2=(%d,%d)" %
                      (a.size + b.size))
            return ret
        else:
            return None

    def __str__(self):
        """Return string representation of self S"""
        return ("Filelist: [%s]\nGammas: [%s]\nMasks: [%s]\nBlurs:"
                "[%s]\nAutoContrasts: [%s]\nRequired number of files:"
                "[%d]\nOutput base dir: [%s]\n" %
                ("\n".join(map(repr, self.filelist)), str(self.gammas),
                 str(self.masks), str(self.blur), str(self.ac), self.noframes,
                 self.outdir))

    def frameAtTime(self, t, fname=None):
        idx, rem = self.filesAtTime(t)
        g = self.gammaAtTime(t)
        blur = self.blurAtTime(t)
        msk = self.maskAtTime(t)
        ac = self.acAtTime(t)
        print("Image t=%f, g=(%f,%f,%f), blur=%f, ac=%f, f1=%s, f2=%s" %
              (t, g[0], g[1], g[2], blur, ac,
               self.filelist[idx].filename, self.filelist[idx + 1].filename))
        result = self.filelist[idx].interp(self.filelist[idx + 1], rem)
        result = imageAutoContrast(result, ac)
        result = imageMask(result, msk)
        result = imageGamma(result, g)
        result = imageBlur(result, blur)
        if fname is not None:
            result.save(fname)
        return result

    def renderLinear(self, nframes=None):
        if nframes:
            self.noframes = nframes
        mint = self.minTime()
        maxt = self.maxTime()
        for n in range(self.noframes):
            t = float(n) / self.noframes * (maxt - mint) + mint
            result = self.frameAtTime(t)
            result.save("%s/result-%05d.%s" % (self.outdir, n, self.outformat))
            [i.reap() for i in self.filelist]

    def renderThreads(self, nthreads=5):
        mint = self.minTime()
        maxt = self.maxTime()
        threads = []
        n = 0
        while n < self.noframes:
            t = float(n) / self.noframes * (maxt - mint) + mint
            idx, rem = self.filesAtTime(t)
            threads.append(
                threading.Thread(target=self.frameAtTime,
                                 args=(t, ("%s/result-%05d.%s" %
                                           (self.outdir, n, self.outformat)))))
            if len(threads) == nthreads:
                [t.start() for t in threads]
                [t.join() for t in threads]
                if idx > 5:
                    [i.reap() for i in self.filelist[:idx - 2]]
                threads = []
            n += 1
        print "Tidying up"
        [t.start() for t in threads]
        [t.join() for t in threads]

    def render(self):
        print "Rendering with %d threads" % self.nothreads
        if self.nothreads == 1:
            self.renderLinear()
        else:
            self.renderThreads(nthreads=self.nothreads)


def test():
    conffile = "test-config.json"
    tl = Timeline(conffile)
    print "Timeline found:\n" + str(tl)
    tl.render()

if __name__ == "__main__":
    test()
