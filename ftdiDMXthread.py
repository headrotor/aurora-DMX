#!/usr/bin/python
# -*- coding: utf-8 -*-

# DMXthread.py
# classes to do the heavy lifting of sending DMX data to usb-RS-485 converters
# in DMX format
# Note: many USB-serial converters (and even some Linux kernels) do not support
# a 250 kBaud serial rate.
# On Linux try apt-get install python-serial
# This has been tested with a FTDI chip and this board:
# CelestialAudio DMX-32

import sys
#import serial

import pylibftdi
# import struct

import time
import math
import colorsys
import Queue
import threading


class sendThread(threading.Thread):
    """Process that listens to queue and if there is a message on it
    (array of bytes), sends it out the serial port in DMX protocol"""
    def __init__(self, ser, queue):
        threading.Thread.__init__(self)
        self.ser = ser
        self.queue = queue

    def run(self):
        while True:
            # get data from queue
            msg = self.queue.get()

           # start the packet by sending a break
            #self.ser.sendBreak(duration=0.0005)

            self.ser.fdti_fn.ftdi_set_line_property2(
                pyftdilib.BITS_8, pyftdilib.STOP_BIT_2, None, 
                pyftdilib.BREAK_ON) 
            time.sleep(0.0005)
            self.ser.ftdi_fn.ftdi_set_line_property2(
                pyftdilib.BITS_8, pyftdilib.STOP_BIT_2, None, 
                pyftdilib.BREAK_OFF) 


            # and send it
            self.ser.write(msg)

            # self.ser.drainOutput()
            self.queue.task_done()

    def flush(self):
        while self.queue.qsize() > 0:
            self.queue.get()
            self.queue.task_done()


class DMXUniverse(object):
    """Class to hold and manage buffer of DMX information and to queue
    it to sendThread worker process"""
    def __init__(self, portname):
        self.portname = portname
        self.verbose = False
        self.check = True  # False to disable range assertions

        # make the byte buffer that will hold the output data
        nullstr = u'00 ' * 513  # must start with null byte
        self.buf = bytearray.fromhex(nullstr)

        # output queue for serial port thread
        self.queue = Queue.Queue()



#         dev_list = []
        
        for device in pylibftdi.Driver().list_devices():
             # list_devices returns bytes rather than strings
            device = map(lambda x: x.decode('latin1'), device)
             # device must always be this triple
            vendor, product, serial = device
            print "%s:%s:%s" % (vendor, product, serial)
            sys.stdout.flush()
        print "libftdi version" + str(pylibftdi.Driver().libftdi_version())


# #dev_list.append("%s:%s:%s" % (vendor, product, serial))
#             #return dev_list
#         return    
    
        #self.s = pylibftdi.Device(device_id="A700eEYl")
        self.s = pylibftdi.Device()
        #with pylibftdi.Device(device_id="A700eEYl") as self.s:
        #with pylibftdi.Device() as self.s:
        print "orig baud" + str(self.s.baudrate)
        self.s.baudrate = 250000
        print "new baud" + str(self.s.baudrate)
        #drv = pylibftdi.Driver()
        #print "libftdi version" + str(drv.libftdi_version())

        self.s.ftdi_fn.ftdi_set_line_property2(
            pyftdilib.BITS_8, pyftdilib.STOP_BIT_2, None, 
            pyftdilib.BREAK_ON) 
        time.sleep(0.0005)
        self.s.ftdi_fn.ftdi_set_line_property2(
            pyftdilib.BITS_8, pyftdilib.STOP_BIT_2, None, 
            pyftdilib.BREAK_OFF) 

        # try:


        #     self.s = serial.Serial(port=portname, baudrate=250000,
        #                            writeTimeout=1.0,
        #                            stopbits=serial.STOPBITS_TWO)
        #     print repr(self.s)

#        except :
#            print 'Unable to open serial port ' + portname
#            self.s = None
            
        # start serial output thread
        self.sendthread = sendThread(self.s, self.queue)
        self.sendthread.setDaemon(True)
        self.sendthread.start()

    def set_chan_int(self, DMX_channel, DMX_value):
        """set this absolute DMX channel to value (absolute channel number)"""

        if self.verbose:
            print 'setting DMX %d to %d' % (DMX_channel, DMX_value)
            sys.stdout.flush()
        if self.check: # are we being picky?
            assert DMX_channel >= 0
            assert DMX_channel < 512
            assert DMX_value < 256
            assert DMX_value >= 0
        self.buf[DMX_channel + 1] = DMX_value

    def __str__(self):
        return '<DMXUniverse %s>' % self.name

    def printbuf(self, start=0, stop=512):
        """print out buffer contents for debugging"""
        for i in range(start, stop):
            if self.buf[i] > 0:
                print 'chan %d val: %d' % (i, self.buf[i])
                sys.stdout.flush()

    def print_buffer(self, start, end):
        """for debugging mostly, oops, duplicate, fix"""
        for i in range(start, end):
            print 'chan %3d val %3d' % (i, int(self.buf[i + 1]))


    def c2int(self, color):
        """convert floating point normalized value [0.0-1.0] to byte"""
        if color > 1.0:
            color = 1.0
        if color < 0:
            color = 0
        return int(color * 255)

    def set_chan_float(self, chan, fval):
        """set the given DMX channel to the given float [0-1] value"""
        self.set_chan_int(chan, self.c2int(fval))

    def send_buffer(self):
        """Queue buffer to DMX output"""
        if self.s:
            qs = self.queue.qsize()
            if qs > 10: # buffer is filling up, print warning
                print 'queue > 10, continuing'
                sys.stdout.flush()
            else:
                print 'sending buffer length ' + str(len(self.buf))
                sys.stdout.flush()
                self.queue.put(self.buf, block=False)

# if running from the console, do some test stuff from the command line
if __name__ == '__main__':

    univ = DMXUniverse('/dev/ttyUSB0')
    if len(sys.argv) < 4:
        print """usage: DMXthread start_chan end_chan val
            sets all DMX channels between start and end-1 to val"""
        exit()
    univ.verbose = True
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    val = int(sys.argv[3])
    for c in range(start, end):
        univ.set_chan_int(c, val)
    univ.send_buffer()

    # don't kill thread until we've done the work!
    time.sleep(0.1)

