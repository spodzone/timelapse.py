#!/usr/bin/env python

from interpimage import *
from timeline import *
import sys


def main():
    conffile = "test-config.json"
    if len(sys.argv) > 1:
        conffile = sys.argv[1]
    tl = Timeline(conffile)
    print "Timeline config:\n" + str(tl)
    tl.render()

if __name__ == "__main__":
    main()
