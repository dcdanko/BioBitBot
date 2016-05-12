import gzip

def openMaybeZip(fname):
	end = fname.split('.')[-1]
	if end == 'gz':
		return( gzip.open(fname))
	else:
		return( open(fname))
