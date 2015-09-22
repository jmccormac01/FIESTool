#!/usr/bin/python

#### User parameters ##############################################

# Where the IRAF/FIEStool login.cl file ?
#logindir="/home/fies-pipe/datared"
logindir="/home/jmcc/"

###################################################################
#
# Invocation: 
#
#   ./imarith.py  FIph030555.fits + FIph030556.fits result1.fits
#   ./imarith.py  FIph030555 + FIph030556 result1
#   ./imarith.py  FIph030555 x FIph030557 result2
#   ./imarith.py  FIph030555 / FIph030558 result3
#   ./imarith.py  FIph030555 - FIph030559 result4
# 
#
# Description:
#  
#   This does IRAF imarith while keeping FITS extensions.  Perfect for
#   adding before and after ThAr-frames, before feeding them to FIEStool.
#
#
# Dependencies:
#  
#    Needs the external IRAF-package MSCRED, in order to maintain 
#    image extensions.
#  
#  
# JHT, Dec 2009
#
###################################################################


from sys import exit, argv
from os  import getcwd, chdir, remove, access, F_OK


# Check syntax
if len(argv) != 5:
  print " Usage:  imarith file1 OPERATOR file2 outfile "
  print " Operators:  '+'  '-'  'x'  '/'  'min'  'max' "
  exit(1)


# Read command-line parameters
file1   =argv[1]
operator=argv[2]
file2   =argv[3]
outfile =argv[4]


# On command line, use 'x' for multiplying instead of '*'
if operator == "x" : operator="*"


# Check for existing output file
if access(outfile,F_OK):
  print " Output file ", outfile, " already exists. Exiting ... \n"
  exit(1)

if access(outfile+'.fits',F_OK):
  print " Output file ", outfile+'.fits', " already exists. Exiting ... \n"
  exit(1)


# Start Pyraf
currentdir = getcwd()
chdir(logindir)
from pyraf import iraf
chdir(currentdir)

# Set some IRAF settings
iraf.set(imtype="fits")


# Load MSCRED
iraf.mscred(_doprint=0,Stdout="/dev/null")


# Do imarith while keeping FITS extensions
iraf.mscred.mscarith(file1,operator,file2,outfile,verbose='yes')

