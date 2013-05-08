aurora-DMX
==========

Python DMX code for driving Aurora LED installation

DMX configuration is specified in config file "mapDMX.cfg"

DMXthread.py: classes for threaded DMX generation in pure python
through a serial port, tested with FTDI USB-RS422 board on Windows and
Raspberry Pi Debian. Can be run from command line to send data to
individual dmx channels (sends 0 to unspecified channels)

aurora.py: Classes for managing irregular structure of Aurora
installation.  Can be run from command line to set a particular branch
on a particular limb to a particular color.

SendImage.py: read an image from the command line, spit it out to DMX
Requires Python Image library: http://www.pythonware.com/products/pil/
usage: Python DMXimage.py testout.png
Can be run in single-step mode using -d flag for debug

testout.png: test image to excercise SendImage.py
