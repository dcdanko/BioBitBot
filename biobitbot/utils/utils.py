import gzip
import math
from biobitbot.plots.sql_data_table import SqlDataTable
import csv

def openMaybeZip(fname):
	end = fname.split('.')[-1]
	if end == 'gz':
		return( gzip.open(fname))
	else:
		return( open(fname))

def percentile(N, percent, key=lambda x:x):
	"""
	Find the percentile of a list of values.

	@parameter N - is a list of values. 
	@parameter percent - a float value from 0.0 to 1.0.
	@parameter key - optional key function to compute value from each element of N.

	@return - the percentile of the values
	"""
	if not N:
		return None
	N = sorted(N)
	k = (len(N)-1) * percent
	f = math.floor(k)
	c = math.ceil(k)
	if f == c:
		return key(N[int(k)])
	d0 = key(N[int(f)]) * (c-k)
	d1 = key(N[int(c)]) * (k-f)
	return d0+d1

def parseDiffExpTable(filename):
	tName = filename.split('/')[-1]
	tName = tName.split('.')[0]
	tName = 'Taxa_{}'.format(tName)
	dt = SqlDataTable(tName)
	with open(filename) as dE:
		header = dE.readline().split()
		if len(header) == 8:
			dt.addColumnInfo('Probe','TEXT')
			dt.ddColumnInfo('logFC','FLOAT')
			dt.addColumnInfo('AveExpr','FLOAT')
			dt.addColumnInfo('t','FLOAT')
			dt.addColumnInfo('P_Value','FLOAT')
			dt.addColumnInfo('adj_P_Val','FLOAT')
			dt.addColumnInfo('B','FLOAT')
			dt.addColumnInfo('gene','TEXT')
		elif len(header) == 9:
			dt.addColumnInfo('logFC','FLOAT')
			dt.addColumnInfo('AveExpr','FLOAT')
			dt.addColumnInfo('t','FLOAT')
			dt.addColumnInfo('P_Value','FLOAT')
			dt.addColumnInfo('adj_P_Val','FLOAT')
			dt.addColumnInfo('B','FLOAT')
			dt.addColumnInfo('group1','TEXT')
			dt.addColumnInfo('group2','TEXT')
			dt.addColumnInfo('taxa','TEXT')
		dt.initSqlTable()
		rdr = csv.reader(dE,delimiter='\t')
		dt.addManyRows(rdr)
	return dt