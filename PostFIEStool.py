# ----------------------------------------------------------------------------------
#								Description
# ----------------------------------------------------------------------------------
#
# PostFIEStool.py - 	a program to continue reductions --> RVs post FIEStool
#	
#						
#

# ----------------------------------------------------------------------------------
# 								Update History
# ----------------------------------------------------------------------------------
# 20/03/13 - 	code writen
# 20/03/13 - 	code tested, waiting results from FF etc
#

from PyJames import *

# first grab the step011 images from the subfolders we want to analyse
# and put them in a folder. rename them to:
#
#	Object_dateobs_timeobs_step.fits
#
# add the original name to a header keyword

base_dir='/Volumes/Storage/FIEStoolShared'
r_dir='/Users/James/data/NOT/TestPostReductions_Aug11/'
folders=['wd_20110823_r','wd_20110824_r','wd_20110825_r','wd_20110826_r']

# go into these folders and copy all the data to a new directory, renaming the files
# as shown above

# step012 = trim[15000:157000] + rename
# step013 = normalise with continuum

iraf=LoadIRAF()


# toggles
grabdata_yn = 0
unzip_yn = 0
fix_headers_yn = 0
trim_rename_yn = 0
tidy_step011_yn = 0
normalise_yn = 0
tidy_step012_yn = 0
run_FXCOR_yn = 1

# get the data
if grabdata_yn > 0:
	for i in range(0,len(folders)):
		data_dir = '%s/%s/reduced/' % (base_dir,folders[i])
		print data_dir
		os.chdir(data_dir)
		t=cmd.getoutput('ls *step011_merge*').split('\n')
		
		for j in range(0,len(t)):
			os.system('cp %s %s' % (t[j],r_dir))
			print "[%d/%d] got %d of %d..." % (i+1,len(folders),j+1, len(t))	

# go to the reduction directory
os.chdir("%s" % r_dir)

# unzip the files if necessary
if unzip_yn > 0:
	os.system('gunzip -rv *.gz')	

# add Jd-mid, MJD-mid, HJD-mid and utmiddle
if fix_headers_yn > 0:
	t=cmd.getoutput('ls *.fits').split('\n')
	
	for i in range(0,len(t)):
		d=pf.open(t[i])[0]
		RA_in=d.header['RA']
		DEC_in=d.header['DEC']
		UT_in=d.header['UT']
		DATE_AVG_in=d.header['DATE-AVG']
	
		YEAR,MONTH,DAY=DATE_AVG_in.split('T')[0].split('-')
		HOUR,MINUTE,SEC=DATE_AVG_in.split('T')[1].split(':')
		
		# RA-N
		ra1=int(RA_in/15.0)
		ra2=int(((RA_in/15.0)%1)*60.0)
		ra3=((((RA_in/15.0)%1)*60.0))%1*60.0
		
		Ra="%02d:%02d:%.2f" % (ra1,ra2,ra3)
		
		# DEC-N
		dec1=int(DEC_in)
		dec2=int((DEC_in%1)*60.0)
		dec3=((DEC_in%1)*60.0)%1*60.0
		
		Dec="%02d:%02d:%.2f" % (dec1,dec2,dec3)
		
		# UT-START
		ut1=int(UT_in)
		ut2=int(UT_in%1*60.0)
		ut3=UT_in%1*60.0%1*60.0
		
		utstart="%02d:%02d:%.2f" % (ut1,ut2,ut3)
		
		#UTMIDDLE
		utmiddle="%02d:%2d:%.2f" % (float(HOUR),float(MINUTE),float(SEC)) 
		
		# hjd-mid and jd-mid
		hjd,jd_e=gethjd(float(YEAR),float(MONTH),float(DAY),float(HOUR),float(MINUTE),float(SEC),float(Ra.split(':')[0]),float(Ra.split(':')[1]),float(Ra.split(':')[2]),float(Dec.split(':')[0]),float(Dec.split(':')[1]),float(Dec.split(':')[2]))
		
		# mjd-mid
		mjd=jd_e-2440000.5
		
		print "RA: %s DEC: %s" % (Ra, Dec)
		print "UT: %s UT-MID: %s" % (utstart,utmiddle)
		print "JDe: %.8f HJD-MID: %.8f" % (jd_e,hjd)
		print "MJD-MID: %.8f\n" % (mjd)
		
		iraf.hedit(images=t[i],fields='RA-N',value='xxx',add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='RA-N',value=Ra,add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='DEC-N',value='xxx',add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='DEC-N',value=Dec,add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='UTSTART',value='xxx',add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='UTSTART',value=utstart,add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='UTMIDDLE',value='xxx',add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='UTMIDDLE',value=utmiddle,add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='HJD-MID',value='xxx',add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='HJD-MID',value="%.8f" % hjd,add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='MJD-MID',value='xxx',add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='MJD-MID',value="%.8f" % mjd,add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='JD-MID',value='xxx',add='yes',verify='no',show='yes')
		iraf.hedit(images=t[i],fields='JD-MID',value="%.8f" % jd_e,add='yes',verify='no',show='yes')
		
# step012, trim and rename 
if trim_rename_yn > 0:
	t=cmd.getoutput('ls *step011_merge*').split('\n')
	
	for i in range(0,len(t)):
		# get tokens for new name ready
		h=pf.open(t[i])[0]
		fobj=h.header['TCSTGT']
		date_avg=h.header['DATE-AVG']
		fdate="%s%s%s" % (date_avg.split('T')[0].split('-')[0],date_avg.split('T')[0].split('-')[1],date_avg.split('T')[0].split('-')[2])
		ftime="%s%s%s" % (date_avg.split('T')[1].split(':')[0],date_avg.split('T')[1].split(':')[1],date_avg.split('T')[1].split(':')[2])
		
		name="%s_%s_%s_step012_trn.fits" % (fobj,fdate,ftime)
		
		iraf.imcopy(input=t[i]+"[15000:157000]",output=name)
		
	t2=cmd.getoutput('ls *step012_trn*').split('\n')
	for i in range(0,len(t2)):
		iraf.hedit(images=t2[i],fields='OLDNAME',value='xxx',add='yes',verify='no',show='yes')
		iraf.hedit(images=t2[i],fields='OLDNAME',value=t[i],add='yes',verify='no',show='yes')


# tidy up step011
if tidy_step011_yn > 0:
	if os.path.exists('step011')==False:
		os.mkdir('step011')
	
	t=cmd.getoutput('ls *step011_merge*').split('\n')
	for i in range(0,len(t)):
		os.system('mv %s step011/' % (t[i]))	

			
# normalise the spectra					
if normalise_yn > 0:
	t=cmd.getoutput('ls *step012_trn*').split('\n')
	
	for i in range(0,len(t)):
		normspec="%s_step013_norm.fits" % (t[i].split('_step012')[0])
		iraf.continuum(input=t[i], output=normspec,logfile="logfile",interac="no", functio="spline3", order="5", niterat="10", markrej="yes")


# tidy up step012		
if tidy_step012_yn > 0:
	if os.path.exists('step012')==False:
		os.mkdir('step012')
	
	t=cmd.getoutput('ls *step012_trn*').split('\n')
	for i in range(0,len(t)):
		os.system('mv %s step012/' % (t[i]))	


# run FXCOR in IRAF for each object
if run_FXCOR_yn > 0:
	
	# load RV module
	iraf.rv(_doprint=0)
	
	iraf.keywpars.setParam('ra','RA') 
	iraf.keywpars.setParam('dec','DEC')
	iraf.keywpars.setParam('ut','UT')
	iraf.keywpars.setParam('utmiddl','UTMIDDLE')
	iraf.keywpars.setParam('exptime','EXPTIME')
	iraf.keywpars.setParam('epoch','OBJEQUIN')
	iraf.keywpars.setParam('date_ob','DATE-OBS')
	
	iraf.keywpars.setParam('hjd','HJD-MID')
	iraf.keywpars.setParam('mjd_obs','MJD-MID')
	#iraf.keywpars.setParam('vobs','VOBS')
	#iraf.keywpars.setParam('vrel','VREL')
	iraf.keywpars.setParam('vhelio','VHELIO')
	#iraf.keywpars.setParam('vlsr','VLSR')
	#iraf.keywpars.setParam('vsun','VSUN')
	#iraf.keywpars.setParam('mode','ql')
	
	iraf.fxcor.setParam('continu','both')
	iraf.fxcor.setParam('filter','none')
	iraf.fxcor.setParam('rebin','smallest')
	iraf.fxcor.setParam('pixcorr','no')
	iraf.fxcor.setParam('apodize','0.2')
	
	iraf.fxcor.setParam('function','gaussian')
	iraf.fxcor.setParam('width','INDEF')
	iraf.fxcor.setParam('height','0.')
	iraf.fxcor.setParam('peak','no')
	iraf.fxcor.setParam('minwidt','3.')
	iraf.fxcor.setParam('maxwidt','21.')
	iraf.fxcor.setParam('weights','1.')
	iraf.fxcor.setParam('backgro','0.')
	iraf.fxcor.setParam('window','INDEF')
	iraf.fxcor.setParam('wincent','INDEF')
	
	iraf.fxcor.setParam('verbose','long')
	iraf.fxcor.setParam('imupdat','no')
	iraf.fxcor.setParam('graphic','stdgraph')
	
	iraf.fxcor.setParam('interac','no')
	iraf.fxcor.setParam('autowri','yes')
	iraf.fxcor.setParam('autodra','yes')
	iraf.fxcor.setParam('ccftype','image')
	iraf.fxcor.setParam('observa','lapalma')
	
	# get list of objects to run through FXCOR
	#objects=["HD115404","HD3765"]
	
	t=cmd.getoutput('ls *.fits').split('\n')
	names=[]
	for i in range(0,len(t)):
		names.append(t[i].split('_')[0])
	
	# make list of unique objects	
	objects=list(set(names))
	
	# run them
	for i in range(0,len(objects)):
		t=cmd.getoutput('ls %s*_step013_norm.fits' % (objects[i])).split('\n')
		
		vshifts=np.empty(len(t))
		spec_names=[]
		
		# write out a file with NAME, JD-MID, HJD-MID, MJD-MID, RV
		f2=file("%s_RVs.lc.txt" % objects[i],"w")
		
		for j in range(0,len(t)):
			template=t[0]
			if j == 0:
				f2.write("Name\tJD-MID\tHJD-MID\tMJD-MD\tRV\n")
				print "Target: %s Ref: %s" % (objects[i],template)
			
			outfile="%s" % (t[j].split('.fits')[0])
	 
	 		iraf.fxcor(objects=t[j],template=template,output=outfile)
	 		
	 		logfile="%s.log" % (outfile)
	
			f=file(logfile,'r')
			s=f.readlines()
			f.close()
			
			vshifts[j]=s[-9].split('=')[1].split(' ')[1]
			print "\t%s\tMeasured Shift: %s Km/s" % (t[j],vshifts[j]) 
			spec_names.append(t[j])
			
			h=pf.open(t[j])[0]
			jd=h.header['JD-MID']
			hjd=h.header['HJD-MID']
			mjd=h.header['MJD-MID']

			f2.write("%s\t%s\t%s\t%s\t%.6f\n" % (t[j],jd, hjd, mjd, vshifts[j]))
			
		f2.close()
	
	
		
		
		
	
	
