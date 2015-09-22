
# ----------------------------------------------------------------------------------
#								Description
# ----------------------------------------------------------------------------------
#
# FIEStoolPrep.py -   a new python program to prepare files for FIEStool
#                     reductions. It will list the objects, associate ThAr arcs	
#				      with the right spectrum, making an average arc and correct 
#                     cosmic rays using JHT's cosmicfilter.py and imarith.py scripts
#                      

# ----------------------------------------------------------------------------------
# 								Update History
# ----------------------------------------------------------------------------------
# 22/01/13 - 	code writen
# 23/01/13 -	code tested
#

import os
import commands as cmd
import pyfits as pf
from os  import getcwd, chdir, remove, access, F_OK


######################################################
################## SETUP VARIBALES ###################
######################################################

# set the directories
wd = "/home/fiestool/host/wd"
reduced = wd + "/reduced"
calibs = reduced + "/calibs"

# cosmic filter params
ybox=7         # the median boxsize in Y direction
threshold=10   # cosmics higher than threshold*STDDEV will be removed


######################################################
##################### FUNCTIONS ######################
######################################################

def TidyTestExps(t):

	if os.path.exists('thartestexps') == False:
		os.system('mkdir thartestexps')
	
	for i in range(0,len(t)):
		OBJECT=pf.open(t[i])[0].header['OBJECT']
		if OBJECT == "EasyThAr count test":
			os.system('mv %s thartestexps' % t[i])
	
	return 0


def LoadIRAF():
	# check for IRAF login file
	if os.path.exists('login.cl') == False:
		os.system('cp ~/login.cl .')
    
	from pyraf import iraf
	x=raw_input('IRAF loaded: Press RETURN')
	
	return iraf


# JHT's cosmicfilter.py code
def CosmicFilter(image,ybox,threshold):
	
	# Determine filename and add ".fits" if necessary
	spos=image.rfind(".fits")
	if spos == -1: spos=len(image)
	image1 = image[0:spos]+".fits"
	
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
	
	# add header keyword
	iraf.hedit(images=image1+"C.fits[0]",fields='RMCOSMIC',value='xxx',add='yes',verify='no',show='yes')
	iraf.hedit(images=image1+"C.fits[0]",fields='RMCOSMIC',value='done using cosmicfilter.py [JHT 09]',add='yes',verify='no',show='yes')
	
	# move unfiltered image to withcosmics
	os.system('mv %s withcosmics/' % image)
	
	print "\n"
	
	return 0


# make average ThAr, put originals in seperate directory
# mscarith line taken from JHT's imarith.py
def AvThAr(ThAr1,ThAr2,operator,ThArAv1,ThArAv):
	
	# check that the ARCSs are really the right ones before combining
	if pf.open(ThAr1+".fits")[0].header['OBJECT'] != pf.open(ThAr2+".fits")[0].header['OBJECT']:
		return 1
	
	# Do imarith while keeping FITS extensions
	# first make a sum of the two images -> ThArAv1
	# then divide ThArAv1 / 2 to get the average
	iraf.mscred.mscarith(ThAr1,operator,ThAr2,ThArAv1,verbose='yes')
	iraf.mscred.mscarith(ThArAv1,"/",2,ThArAv,verbose='yes')
	
	iraf.hedit(images=ThAr1+"A.fits[0]",fields='THARCOMB',value='xxx',add='yes',verify='no',show='yes')
	iraf.hedit(images=ThAr1+"A.fits[0]",fields='THARCOMB',value='Combined ThAr from (%s+%s)/2' % (ThAr1,ThAr2),add='yes',verify='no',show='yes')
	
	os.system('mv %s.fits uncombinedarcs/' % ThAr1)
	os.system('mv %s.fits uncombinedarcs/' % ThAr2)
	os.system('rm -rf %s.fits' % ThArAv1)
	
	return 0
	
	
# zip the data not being used
def ZipUnusedFiles():
	
	os.system('gzip -rv9 thartestexps/')
	os.system('gzip -rv9 uncombinedarcs/')
	os.system('gzip -rv9 withcosmics/')
	
	return 0


######################################################
####################### MAIN #########################
######################################################

# toggles
mkdirs_yn = 1
tidytestexps_yn = 1
combinearcs_yn = 1
fixcosmics_yn = 0
zipfiles_yn = 0


if mkdirs_yn > 0:
	# go to wd
	os.chdir(wd)
	
	# make the reduced and calibs directories
	if os.path.exists(reduced) == False:
		os.mkdir(reduced)
	if os.path.exists(calibs) == False:
		os.mkdir(calibs) 
	
# get list of images
t=cmd.getoutput('ls *.fits').split('\n')

# empty lists for things
object_list = []
object_file_list = []
list_num = []

# load IRAF
iraf=LoadIRAF()
iraf.set(imtype="fits")

# Load MSCRED
iraf.mscred(_doprint=0,Stdout="/dev/null")

if tidytestexps_yn > 0:
	# put "EasyThAr count test" exposures in a seperate directory
	f1=TidyTestExps(t)

# get new list without ThAr Test Exposures getting in the way
t2=cmd.getoutput('ls *.fits').split('\n')

# loop over files sorting them into lists
for i in range(0,len(t2)):
	h=pf.open(t2[i])
	TCSTGT=h[0].header['TCSTGT']
	OBJECT=h[0].header['OBJECT']
	
	print "%s\t%s\t%s" % (t2[i],TCSTGT,OBJECT)
	
	# Interleaved ThAr exposures have OBJECT names
	# "ThAr OBJECT"
	if "ThAr" not in OBJECT and "flat" not in OBJECT and "FLAT" not in OBJECT and "bias" not in OBJECT and "EasyHalo" not in OBJECT and "halogen" not in OBJECT and OBJECT != ' ':
		object_list.append(OBJECT)
		object_file_list.append(t2[i])
		list_num.append(i)


yn=raw_input("Review the frame list:\n\tPress ENTER to continue\n\tPress q to quit\n")
if yn == 'q':
	exit()
	
# display the object lists to check
for i in range(0,len(object_list)):
	print "%s\t%s\t%s" %(object_file_list[i],object_list[i],list_num[i])

yn=raw_input("Review the object list:\n\tPress ENTER to continue\n\tPress q to quit\n")
if yn == 'q':
	exit()	


# combining arcs operator		
operator = "+"

# fix cosmics
# associate each objects ThAr frames with it
# and make an average arc, tidy up unprocessed frames
# and compress unused data
for i in range(0,len(object_list)):
	
	if combinearcs_yn > 0:
		# ThAr files are the ones either side with the ThAr Test Exposures
		# moved out of the way
		ThAr1=t2[list_num[i]-1]
		ThAr2=t2[list_num[i]+1]
		
		print "\n--------------------------------------------------------------------------------"	
		print "\n[%03d] %s\t%s ThAr(%s\t%s)" % (int(list_num[i]+1),object_list[i],object_file_list[i],ThAr1,ThAr2)
		print "\n--------------------------------------------------------------------------------"	
	
	if fixcosmics_yn > 0:	
		# call JHT's cosmicfilter.py script
		# put raw images into dir withcosmics
		if os.path.exists('withcosmics') == False:
			os.system('mkdir withcosmics')
		
		print "\nFixing cosmic rays in %s..." % (object_file_list[i])
		f1=CosmicFilter(object_file_list[i],ybox,threshold)
	
	if combinearcs_yn > 0:	
		# put uncombined arcs to uncombinedarcs
		if os.path.exists('uncombinedarcs') == False:
			os.system('mkdir uncombinedarcs')
		
		ThArAv1="%sA1" % (ThAr1.split('.')[0])
		ThArAv="%sA" % (ThAr1.split('.')[0])
		print "Combining (%s + %s)/2 = %s.fits" % (ThAr1,ThAr2,ThArAv)
		f2=AvThAr(ThAr1.split('.')[0],ThAr2.split('.')[0],operator,ThArAv1,ThArAv)
		
		if f2 == 1:
			print "\nTARGET for %s and %s are NOT the same, exiting...\n" % (ThAr1,ThAr2)
			exit()

if zipfiles_yn > 0:	
	# zip up unused data at the end
	f3=ZipUnusedFiles()
	
	
