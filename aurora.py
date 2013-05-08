#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file contains classes to deal with the irregular structure of
 the Aurora artwork

 "PODs" are a group of 4 DMX-32 boards, each pod can support up to
 4x32=128 DMX channels; at three channels per branch or 10 branches
 per board, each pod can support 40 branches.

 One DMX universe can only support 4 pods, labled A,B,C,D so the fifth
 "E" pod is on a separate DMX universe."""


import sys
import struct
import time
import math
import colorsys
import ConfigParser

# local classes
import DMXthread


class Pod(object):

    """Class to support a group of 4 DMX-32 boards"""

    def __init__(self, name, universe):
        self.name = name
        self.universe = universe
        self.limbs = []  # array of Limb structures

    def printInfo(self):
        print 'pod %s, num limbs: %d' % (self.name, len(self.limbs))


# A "Limb" is a group of branches on the same physical pipe ("limb")
# It can have anywhere from 5 to 11 branches.

class Limb(object):

    """Class to support "limb" structure in Aurora, can have 5-11 branches"""

    def __init__(self, name, nbranches):
        self.name = name
        self.branches = [Branch(0, 0, 0, 0, (0, 0, 0)) for n in
                         range(nbranches)]

    def printInfo(self):
        print '   limb %s, num branches: %d' % (self.name,
                len(self.branches))

    def addBranch(self, n, branch):
        self.branches[n] = branch


# A "branch" is the simplest light unit, it is a single strip of RGB
# LED and can be set to any RGB color. There are 5-11 branches per
# limb and up to 40 branches per pod.

class Branch(object):

    def __init__(
        self,
        name,
        start,
        uni,
        board,
        channels,
        ):
        self.name = name
        self.start = start  # start address of this branch
        self.brindex = 0  # branch index
        self.board = board  # board in pod
        self.universe = uni  # universe of this branch from parent bd
        self.channels = channels  # triple of board-level channels (0-31)
        if max(self.channels) > 32:
            print 'ERROR: channel value out of range for branch ' + name
            exit()

    # calculate DMX channel from start offset plus local channel

        self.DMX = [c + self.start - 1 for c in self.channels]
        if max(self.DMX) > 511:
            print 'WARNING: DMX value out of range for branch ' + name
            exit()

    # self.xypos                 # tuple of x, y position

    def __str__(self):
        return '%s index %3s, bd: %d chan: %12s DMX[%s]: %s' % (
            self.name,
            self.brindex,
            self.board,
            self.channels,
            self.universe,
            self.DMX,
            )

    def printInfo(self):
        print self.__str__()

    def setNextColor(self, hsv):
        """ Set a new color for interpolation"""

        self.lastHSV = self.thisHSV
        self.thisHSV = hsv

    def getTweenColor(self, factor):
        """return interpolated color from last color and this color"""

        pass

    def getLimbIndex(self):
        """parse name to get limb index, eg A-2-4 is limb 2 (actually
        [1])"""

        data = self.name.split('-')
        return int(data[1]) - 1

    def getBranchIndex(self):
        """parse name to get br number on limb, eg A-2-4 is branch 4
        (actually [3])"""

        data = self.name.split('-')
        return int(data[2])


class AuroraDMX(object):
    """AuroraDMX: class to support aurora dmx from config file
     Nomenclature: a pod supports 40 branches there are 5 a board
     supports 10 branches, there are 20 a branch is one strip, or
     three DMX channels"""

    def __init__(self, cfgfile):
        self.branches = []  # list of brancj structs
        self.InitFromCfg(cfgfile)
        self.uni0 = DMXthread.DMXUniverse(self.universes[0])
        self.DMX = [self.uni0]  # array of DMX devices, 1 per universe
        if len(self.universes) > 1:
            self.uni1 = DMXthread.DMXUniverse(self.universes[1])
            self.DMX.append(self.uni1)
        else:
            self.uni1 = None

    def TreeSend(self, dstart=0, dend=0):
        self.uni0.send_buffer()
        if self.uni1 is not None:
            self.uni1.send_buffer()

    def setChan(
        self,
        u,
        chan,
        fval,
        ):
        """ set the given channel to the given [0-1] floating value"""

        self.DMX[u].set_chan_float(chan, fval)

    def setChanInt(
        self,
        u,
        chan,
        intval,
        ):
        """ set the given channel to the given [0-255] int value"""

    # print "setting chan %d to %d" % (chan,intval)
    # sys.stdout.flush()

        self.DMX[u].set_chan_int(chan, intval)

    def setBranchInt(self, branch, rgb):
        """ set the three branch channels to the given RGB values """

        u = self.branches[branch].universe
        if u < len(self.DMX):
            self.setChanInt(u, self.branches[branch].DMX[0], rgb[0])
            self.setChanInt(u, self.branches[branch].DMX[1], rgb[1])
            self.setChanInt(u, self.branches[branch].DMX[2], rgb[2])
        else:

      # print "Warning: universe %d out of range" % u

            pass

    def setBranchRGB(self, branch, rgb):
        """ set the three branch channels to the given RGB values """

        u = self.branches[branch].universe
        if u < len(self.DMX):
            self.setChan(u, self.branches[branch].DMX[0], rgb[0])
            self.setChan(u, self.branches[branch].DMX[1], rgb[1])
            self.setChan(u, self.branches[branch].DMX[2], rgb[2])
        else:

      # print "Warning: universe %d out of range" % u

            pass

    def setBranchHSV(self, branch, hsv):
        """ set the branch to the given hue, sat, and value (bright) triple"""
        self.setBranchRGB(branch, colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2]))

    def InitFromCfg(self, cfgfile):
        """ initialize all data structures from configuration file """

        self.cfg = ConfigParser.RawConfigParser()
        self.cfg.read(cfgfile)

      # how many universes? read any config items starting with "universe"

        universes = [item[1] for item in self.cfg.items('DMX')
                     if item[0].startswith('universe')]

        if len(universes) < 1:
            print 'no universes detected in config file! Bye.'
            exit()

        self.universes = universes
        print repr(universes)

        board_count = 0

    # get a list of pods

        podnames = self.cfg.get('pods', 'pods')
        podnames = podnames.split(',')

        self.pods = []

        for p in podnames:

            pname = 'pod' + p
            uni = self.cfg.getint(pname, 'universe')
            new_pod = Pod(pname, uni)

            # first, get start addresses of all boards
            nboards = len([item[1] for item in self.cfg.items(pname)
                          if item[0].startswith('board')])
            starts = [0] * nboards
            bnames = [(n, 'board' + str(n)) for n in range(nboards)]
            for (n, b) in bnames:
                starts[n] = self.cfg.getint(pname, b)

            #print 'pod ' + new_pod.name

            # get ordered list of limbs
            lnames = ['branch-1', 'branch-2', 'branch-3', 'branch-4',
                      'branch-5']

            for lname in lnames:  # for each limb

                # get list of branch names for this limb (ending with A, eg)
                lbrnames = [item[0] for item in self.cfg.items(pname)
                            if item[0].startswith(lname)]

                nbranches = len(lbrnames)
                if nbranches > 0:

                    # now we have list of branch names for this limb.
                    # make a new limb with this many branches
                    limb = Limb(p + lname, nbranches)

                    # now for every branch in this limb, add it to the Limb
                    for brname in lbrnames:

                        data = self.cfg.get(pname, brname)
                        data = [int(k) for k in data.split(',')]

                        # data is a list of [board, rchan,bchan,gchan]
                        board = data[0]
                        start = starts[board]  # start address for this branch

                        new_branch = Branch(p + brname, start, uni,
                                board, (data[1], data[2], data[3]))

                        data = brname.split('-')
                        index = int(data[2])

                        # print "adding branch %d" % index + new_branch.name
                        limb.addBranch(index, new_branch)

                        sys.stdout.flush()
                    new_pod.limbs.append(limb)
            self.pods.append(new_pod)

        # all boards read in. Now create list of limbs and branches[]
        brcount = 0
        self.branches = []
        self.limbs = []
        self.limblist = []
        for pod in self.pods:
            self.limbs.append(pod.limbs)
            self.limblist.extend(pod.limbs)
            for lb in pod.limbs:
                for br in lb.branches:
                    br.brindex = brcount
                    self.branches.append(br)
                    brcount += 1

    def print_config(self):
        """ print the dmx configuration """
        for pod in self.pods:
            for lb in pod.limbs:
                print '%s limb %s ' % (pod.name, lb.name)
                for br in lb.branches:
                    br.printInfo()
        sys.stdout.flush()

# if running from the console, do some test stuff
if __name__ == '__main__':

    # make the DMX data structure from the config file
    treeDMX = AuroraDMX('mapDMX.cfg')

    # print it out for debug
    if sys.argv[1] == 'c':
        treeDMX.print_config()
        exit()

    if len(sys.argv) < 4:
        print """usage: aurora.py l b color
 sets limb l on branch b (ints) to color where 
 color is one of red, blue, green, white, off, cyan, magenta, yellow"""
        exit()

    if sys.argv[3][0] == 'r':
        color = (255, 0, 0)
    elif sys.argv[3][0] == 'g':
        color = (255, 0, 0)
    elif sys.argv[3][0] == 'b':
        color = (0, 0, 255)
    elif sys.argv[3][0] == 'w':
        color = (255, 255, 255)
    elif sys.argv[3][0] == 'o':
        color = (0, 0, 0)
    elif sys.argv[3][0] == 'c':
        color = (0, 255, 255)
    elif sys.argv[3][0] == 'm':
        color = (255, 0, 255)
    elif sys.argv[3][0] == 'y':
        color = (255, 255, 0)
    else:

        print 'unrecognized color "%s"' % sys.argv[3]
        exit()

    limb = int(sys.argv[1])
    branch = int(sys.argv[2])

    l = treeDMX.limblist[limb]
    b = l.branches[branch]
    print str(b)

    treeDMX.setBranchRGB(b.brindex, color)
    sys.stdout.flush()
    treeDMX.TreeSend()
    time.sleep(0.1)  # give threads a chance to work

