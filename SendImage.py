# SendImage.py: read an image from the command line, spit it out to DMX
# Requires Python Image library: http://www.pythonware.com/products/pil/
# usage: Python SendImage.py test.png

import Image
import sys
import os
import time
import colorsys
from optparse import OptionParser

#local classes
import aurora

class ImageData(object):
  """import an image as a data source for the DMX. """
  """Needs Python Image Library (PIL) http://www.pythonware.com/products/pil/"""
  def __init__(self, filename, cols):
    """open the image in filename. Only use 'cols' columns"""
    self.cols = int(cols)
    try:
      self.img = Image.open(filename) 
    except:
      print "unable to open image" + filename
      exit()
    print "loaded %d x %d image " % (self.img.size[0],self.img.size[1]) + filename  
    if self.img.size[0] < self.cols:
      print "WARNING: image undersized. Resizing to %d x %d" % (cols,self.img.size[1])
      self.img = self.img.resize((self.cols,self.img.size[1]))
    data = self.img.load()  
    self.x = self.img.size[0]
    self.y = self.img.size[1]
    self.rows = []

    # now make a list of pixel rows in HSV space *.py
    for j in range(self.y):
      row = []
      for i in range(self.cols):
        # strip off alpha channel if any and convert to [0-1] float
        pixel = [float(p)/255.0 for p in data[i,j][0:3]]
        #row.append(colorsys.rgb_to_hsv(pixel[0],pixel[1],pixel[2]))
        #row.append((pixel[0],pixel[1],pixel[2]))
        row.append([ p for p in data[i,j][0:3]])
      self.rows.append(row)  

  def getrow(self,r):
    """ return a row of data from the image as a list of HSV tuples"""
    return(self.rows[r])

  def getrowinterp(self,r,f):
    """Get a row of images interpolated from previous row by factor f"""
    if r == 0:
      prevrow = [(0,0,0)] * len(self.rows[r])
    else:
      prevrow = self.rows[r-1]
      
    irow = []
    ic = [0]*3
    for i, pixel in enumerate(self.rows[r]):
      for j in range(len(pixel)):
        ic[j] = int(f*pixel[j] + (1-f)*prevrow[i][j])
      irow.append(ic)
    return(irow)
      

ticks = time.clock()

def waitrate(frate):
  """ Wait for 1/framerate of a second since the last time we called"""
  global ticks
  delay = float(1/float(frate))
  elapsed = time.clock() - ticks
  sleeptime = delay - elapsed
  if sleeptime > 0:
    time.sleep(sleeptime)

  ticks = time.clock()




def main():
    usage = "usage: %prog [options] imagefile"
    parser = OptionParser(usage)
    parser.add_option("-c", "--config_file", dest="cfgfile",
                      help="read configuration file from FILENAME",
                      default="mapDMX.cfg")
    parser.add_option("-i", "--interpolate", type="int", dest="interpolate",
                      help="interpolate this many frames",
                      default=1)
    parser.add_option("-r", "--repeat", type="int", dest="repeat",
                      help="repeat count, 0 to repeat forever",
                      default=1)
    parser.add_option("-z", "--zigzag", type="int", dest="zigzag",
                      help="repeat boustrophedonically",
                      default=1)
    parser.add_option("-f", type="float", dest="framerate",
                      help="output frame rate",
                      default=20.0)
    parser.add_option("-d", "--debug",
                      help="interactive mode for debug",
                      action="store_true", dest="interactive")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("Expecting image file name")

 
    print "using config file %s" % options.cfgfile
    # make the DMX data structure from the config file
    treeDMX = aurora.AuroraDMX(options.cfgfile)


    #for br in treeDMX.branches:
    #  br.printInfo()


    if options.verbose:
      treeDMX.print_config()
      print "number of branches: " + str(len(treeDMX.branches))

    # make list of image files 
    filenames = []
    if os.path.isdir(args[0]):  # if it's a directory, harvest it
      for f in os.listdir(args[0]):
        fname = os.path.join(args[0], f)
        if os.path.isfile(fname):
          filenames.append(fname)
       
    else:
      filenames.append(args[0])

    if options.repeat == 0:
      finite = False
      repeat = 1
    else:
      finite = True
      repeat = options.repeat

    while(repeat > 0):
      if finite:
        repeat -= 1


     
      for f in filenames:
        print "reading file " + f
        sys.stdout.flush()

        # load the image file and convert to HSV
        imd = ImageData(f,len(treeDMX.branches))


        start = time.clock()

        if options.interactive:
          foo = sys.stdin.read(1)

        for r in range(imd.y):
          for i in range(options.interpolate):
            if options.interpolate == 1:
              row = imd.getrow(r)
            else: # cross-fade from previous frame
              row = imd.getrowinterp(r,i/float(options.interpolate))
              
            for b, pixel in enumerate(row):
              # set each branch to the corresponding pixel in this row
              #treeDMX.setBranchRGB(b,pixel)
              brindex = treeDMX.branches[b].brindex
              treeDMX.setBranchInt(brindex,pixel)
              #print str(b)
            treeDMX.TreeSend()

            if options.interactive:
              #foo = raw_input('next>') 
              foo = sys.stdin.read(1)
              print "sent row %d of %d" % (r+1,imd.y)
              treeDMX.uni0.printbuf(0,15)
            else:
              waitrate(options.framerate)
        delta = time.clock() - start

        print "sent %d frames interpolated to %d in %4.2fs, frame rate = %f" \
            % ((r),r*options.interpolate,delta,(r*options.interpolate/delta))
        sys.stdout.flush()



# console based program: give it an image file name as a first argument
if __name__=='__main__':

  main()

