#!/usr/bin/python

#### User parameters ##############################################

ybox=7         # The median boxsize in Y direction
threshold=10   # Cosmics higher than threshold*STDDEV will be removed

# Where is the IRAF/FIEStool login.cl file ?
#logindir="/home/fies-pipe/datared"
logindir="/Users/James/"

###################################################################
#
# Invocation: 
#
#   ./cosmicfilter.py  FIph030555
#   ./cosmicfilter.py  FIph030555.fits
#
# Purpose:
#
#   filter cosmics from a single FIES object frame.
#   Works also for AB mode.
#
#
# Description:
#  
#   There are 2 parameters that may be tweaked:
#   - YBOX
#   - THRESHOLD
#  
#  
#   Reduction steps:
#
#   - make median image with X,Y boxsize  1,YBOX 
#
#   - make residualImage = originalImage - medianImage
#
#   - iteratively compute STDDEV in residualImage (excluding cosmics)
#
#   - replace cosmics in residualImage  by zero.
#     Cosmics higher than THRESHOLD*STDDEV will be removed
#
#   - construct final image from medianImage and filtered residualImage 
#  
#  
# Output: 
#    
#    A file named "<inputfile>C.fits" will be generated
#  
#  
# Dependencies:
#  
#    Needs the external IRAF-package MSCRED, in order to maintain 
#    image extensions.
#  
#  
# To check the result use
#
#   ds9 -zscale FIph030555C.fits FIph030555.fits -blink
#  
#
# JHT, Dec 2009
#
###################################################################



from sys import exit, argv
from os  import getcwd, chdir, remove, access, F_OK

# Check syntax
arglist=argv[1:]
nparam=len(arglist) 

if nparam != 1:
  print " Examples:  ./cosmicfilter.py FIpk110123"
  print "            ./cosmicfilter.py FIpk110123.fits\n"
  exit(1)


# Start Pyraf
currentdir = getcwd()
chdir(logindir)
from pyraf import iraf
x=raw_input('IRAF loaded: Press RETURN')
chdir(currentdir)


# Determine filename and add ".fits" if necessary
spos=arglist[0].rfind(".fits")
if spos == -1: spos=len(arglist[0])
image1 = arglist[0][0:spos]+".fits"


# Quit if the file does not exist
if not access(image1,F_OK): 
  print " FIES image "+image1+" not found!"
  exit(1)


# Strip ".fits" extension
image1 =image1[0:spos]


# Quit if any of the output files do exist
doexit=0
if access(image1+"CosmicFilt-r.fits",F_OK): 
  print " FIES image "+image1+"CosmicFilt-r.fits already exists!"
  doexit=1
if access(image1+"CosmicFilt-m.fits",F_OK): 
  print " FIES image "+image1+"CosmicFilt-m.fits already exists!"
  doexit=1
if access(image1+"C.fits",F_OK): 
  print " FIES image "+image1+"C.fits already exists!"
  doexit=1

if doexit==1:
  exit(1)


# Set some IRAF settings
iraf.set(imtype="fits")
#iraf.images(Stdout="/dev/null")
#iraf.images.imutil(Stdout="/dev/null")


# Check some headers
object    =iraf.images.imutil.hselect(image1+"[0]", "OBJECT", "yes", Stdout=1)[0]
tcstgt    =iraf.images.imutil.hselect(image1+"[0]", "TCSTGT", "yes", Stdout=1)[0]
tophalogen=iraf.images.imutil.hselect(image1+"[0]", "FILMP6", "yes", Stdout=1)[0]
bothalogen=iraf.images.imutil.hselect(image1+"[0]", "FILMP1", "yes", Stdout=1)[0]
topthar   =iraf.images.imutil.hselect(image1+"[0]", "FILMP7", "yes", Stdout=1)[0]
botthar   =iraf.images.imutil.hselect(image1+"[0]", "FILMP4", "yes", Stdout=1)[0]
maskpos   =iraf.images.imutil.hselect(image1+"[0]", "FIFMSKNM", "yes", Stdout=1)[0]
armpos    =iraf.images.imutil.hselect(image1+"[0]", "FICARMNM", "yes", Stdout=1)[0]

print "OBJECT        ",object
print "TCS target    ",tcstgt
print "\nArm                   ", armpos
print "Mask                  ", maskpos
print "Top Halogen    (0/1)  ", tophalogen
print "Bottom Halogen (0/1)  ", bothalogen
print "Top ThAr       (0/1)  ", topthar
print "Bottom ThAr    (0/1)  ", botthar


if (topthar==1) | (tophalogen==1) | (botthar==1) | (bothalogen==1):
  print "\nThis task should not be run on FIES frames with lamp light.\n"
  exit(0)



############ Start data reduction ###########

iraf.mscred(Stdout="/dev/null")

print "\nKilling strong cosmics ..."

print "     making '+ybox+'-point median ..."
iraf.mscred.mscmedian(image1,image1+"CosmicFilt-m",1,ybox,fmedian='no',verbose="no")

print "     making residual image ..."
iraf.mscred.mscarith(image1,"-",image1+"CosmicFilt-m",image1+"CosmicFilt-r",verbose="no")

lines=iraf.images.imutil.imstat(image1+"CosmicFilt-r[1]",field="stddev",nclip=1,Stdout=1)
print "     StdDev in filtered image ", float(lines[1])
threshold=threshold*float(lines[1])

print "     removing spikes ( > ", threshold," ADU) from residual image ..."
iraf.images.imutil.imreplace(image1+"CosmicFilt-r[1]",0,lower=threshold)

print "     removing spikes from original image ..."
iraf.mscred.mscarith(image1+"CosmicFilt-r","+",image1+"CosmicFilt-m",image1+"C",verbose="no")
print "     created file "+image1+"C.fits"

print "     removing temporary files  *CosmicFilt*  ..."
remove (image1+"CosmicFilt-r.fits")
remove (image1+"CosmicFilt-m.fits")

print "\n"
