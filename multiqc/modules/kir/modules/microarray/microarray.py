#!/usr/bin/env python

""" MultiQC module to parse output from CGAT Microarray Differential Expression Pipeline"""


from collections import OrderedDict
import logging
import re
import csv
from multiqc import config, BaseMultiqcModule
from multiqc.plots.sql_data_table import SqlDataTable
import multiqc.plots.scatterplot as scatter
import multiqc.plots.boxplot as boxplot
import math
from random import random

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):

	def __init__(self):

		# Initialise the parent object
		super(MultiqcModule, self).__init__(name='Microarray Analysis', anchor='microarray',  
		info="Displays the results of differential expression analysis on a microarray")

		self.setMetadata()
		self.parseDataFiles()
		self.makeProbeGeneMaps()

		self.sections = []
		self.buildPCACharts()
		self.buildSignifPlots()

	def setMetadata(self):
		metaF = [f for f in self.find_log_files(config.sp['microarray']['metadata'])]
		assert len(metaF) == 1
		with openMaybeZip(metaF[0]['fn']) as mF:
			metadata = yaml.load(mF)
			self.conditions = metadata['conditions']

	def parseDataFiles(self):
		diff_exp_files = [f for f in self.find_log_files(config.sp['microarray']['diff_exp'])]
		self.diff_exp_tables = [parseDiffExpTable(f['fn']) for f in diff_exp_files]

	# def parseTables(self):
	# 	diffFiles = [dF for dF in self.find_log_files(config.sp['microarray']['diff_exp'])]
	# 	print(diffFiles)
	# 	assert len(diffFiles) == 1
	# 	self.diffExp = self.parseDiffExpTable(diffFiles[0]['fn'])

	# 	rawFiles = [rF for rF in self.find_log_files(config.sp['microarray']['norm_exp'])]
	# 	print(rawFiles)
	# 	assert len(rawFiles) == 1
	# 	self.rawData = self.parseRawDataTable(rawFiles[0]['fn'])

	def makeProbeGeneMaps(self):
		probemap = [f for f in self.find_log_files(config.sp['microarray']['probemap'])]
		assert len(probemap) == 1
		with openMaybeZip(probemap[0]['fn']) as pM:
			pM.readline()
			self.probeToGenes = {}
			self.genesToProbes = {}
			for line in pM:
				probe, gene = [el.strip().strip('"') for el in line.split()]
				self.probeToGenes[probe] = gene
				if gene not in self.genesToProbes:
					self.genesToProbes[gene] = [probe]
				else:
					self.genesToProbes[gene].append(probe)

	def buildPCACharts(self):
		axes_interest = 4


		pts = [f for f in self.find_log_files( config.sp['metagenomics']['pca']['points'])]
		pts = pts[0]['fn']
		points = {}
		with open(pts) as pF:
			pF.readline()
			for line in pF:
				line = line.split()
				# print(line)
				sample = self.getSampleFromFilename('-'.join(line[0].strip().split('.')))
				vals = [float(pt) for pt in line[1:]]
				points[sample] = vals[:axes_interest]

		ve = [f for f in self.find_log_files( config.sp['metagenomics']['pca']['variance'])]
		ve = ve [0]['fn']
		with open(ve) as vF:
			vF.readline()
			axes = [float(axis) for axis in vF.readline().split()]
			axes = axes[:axes_interest]

		plotDatasets = OrderedDict()
		for i,j in itertools.combinations(range(axes_interest),2):
			plotData = {}
			for condition, samples in self.conditions.items():
				plotData[condition] = []
				for sample in samples:
					x = points[sample][i]
					y = points[sample][j]
					plotData[condition].append({'x':x,'y':y})
			plotDatasets['{}_{}'.format(i,j)] = plotData	

		plots =[]
		for iName, plotData in plotDatasets.items():
			i,j = [int(v) for v in iName.split('_')]
			plot = scatter.plot(plotData, pconfig={
												'ylab':'PC{} ({:.1f}%)'.format(j+1,100*axes[j]), 
												'xlab':'PC{} ({:.1f}%)'.format(i+1,100*axes[i]), 
												'title':'Principal Components {} and {}'.format(i+1,j+1),
												'legend': True
												})
			plots.append(plot)	

		plot = 	"""
				<p>The first {} principal components which explain {:.1f}% of the variation in the data.</p>
				""".format(axes_interest, 100*sum(axes))
		htmlRows = []
		rowSize = 3
		for i, aPlot in enumerate(plots):
			if i % rowSize == 0:
				htmlRows.append([""]*rowSize)
			htmlRows[i / rowSize][i % rowSize] = aPlot

		plot += split_over_columns(htmlRows,rowwise=True)



		self.sections.append({
			'name' : 'Principal Component Analysis',
			'anchor' : 'pca_charts',
			'content' : plot
			})

	# def buildGeneBoxPlots(self):
	# 	cols, rows = self.diffExp.getTable(sqlCmd="SELECT gene FROM {table_name}  WHERE adj_P_val < 0.1 AND logFC > 0.5")
	# 	genes = {}
	# 	for gene in rows:
	# 		genes[gene] = True
	# 	htmlRows = []
	# 	rowSize = 2
	# 	for i,gene in enumerate(genes.keys()):
	# 		if i % rowSize == 0:
	# 			htmlRows.append([""]*rowSize)
	# 		gene = gene[0]
	# 		htmlRows[i / rowSize][i % rowSize] = self.geneBoxPlot(gene,isgene=True)
	# 	html_str = split_over_columns(htmlRows, rowwise=True)
	# 	self.sections.append({
	# 		'name' : 'Gene Expression Levels',
	# 		'anchor' : 'gene_exp_lvls',
	# 		'content' : html_str
	# 		})

	# def buildDiffExpTable(self):

	# 	html_str = self.diffExp.as_html(sqlCmd="SELECT  * FROM {table_name} WHERE adj_P_Val < 0.005 AND AveExpr > 8")
	# 	self.sections.append({
	# 		'name' : 'Differential Expression',
	# 		'anchor' : 'diff_exp',
	# 		'content' : html_str
	# 		})

	def buildSignifPlots(self):

		def oneVolcanoPlot(table,conditions,minLfc=0.5,maxApv=0.1,rarefier=0.1):
			cols, rows = table.getTable(sqlCmd="SELECT gene, logFC, adj_P_Val, group1, group2 FROM {table_name} ")


			lava = {'not significant (rarefied)':[], 'significant':[]}
			for gene, lfc, apv, g1, g2 in rows:
				if abs(lfc) > minLfc and apv < maxApv:
					lava['significant'].append({'name':gene, 'x':lfc, 'y':-math.log(apv,2)})
				elif random() <  rarefier: # rarify insignificant points so page loads faster 
					lava['not significant (rarefied)'].append([lfc,-math.log(apv,2)])

			return scatter.plot(lava, pconfig={
												'ylab':'Negative log of adjusted p value', 
												'xlab':'average log fold change', 
												'title':'Volcano Plot {} v. {}'.format(*conditions),
												'legend':True
												})

		def oneMaPlot(table,conditions,minLfc=0.5,maxApv=0.1,rarefier=0.1):
			cols, rows = table.getTable(sqlCmd="SELECT gene, logFC, adj_P_Val, AveExpr, group1, group2 FROM {table_name} ")

			lava = {'not significant (rarefied)':[], 'significant':[]}
			for  gene, lfc, apv, aE, g1, g2 in rows:
				if abs(lfc) > minLfc and apv < maxApv:
					lava['significant'].append({'name':gene, 'y':lfc, 'x':aE})
				elif random() <  rarefier: # rarify insignificant points so page loads faster 
					lava['not significant (rarefied)'].append([aE,lfc])

			return scatter.plot(lava, pconfig={
												'ylab':'Ave. Log Fold Change', 
												'xlab':'Ave. Expression', 
												'title':'MA Plot {} v. {}'.format(*conditions),
												'legend':True
												})


		sigPlots = []
		for diff_exp_table in self.diff_count_tables:
			conditions = self.getConditionsFromFilename(diff_exp_table.name)
			volcano = oneVolcanoPlot(diff_exp_table,conditions)
			ma 		= oneMaPlot(diff_exp_table,conditions)
			sigPlots.append( (volcano,ma))


		plot = """
				<p>Volcano and MA plots under various conditions</p>
				"""
		plot += split_over_columns(sigPlots,rowwise=True)

		self.sections.append({
			'name' : 'Significance Plots',
			'anchor' : 'sig_plots',
			'content' : plot
			})

	# def buildSigPlots(self):
	# 	volcs = self.volcanoPlot()
	# 	mas = self.maPlot()
	# 	html_str = split_over_columns([[volcs],[mas]])
	# 	self.sections.append({
	# 		'name' : 'Significance Plots',
	# 		'anchor' : 'sig_plots',
	# 		'content' : html_str
	# 		})

	# def geneBoxPlot(self, probe, isgene=False):
	# 	pconfig = {'ylab':'Expression Level', 'xlab':'Condition', 'title':'{} Expression Levels'.format(probe)}
	# 	if not isgene:
	# 		cols, rows = self.rawData.getTable(sqlCmd="SELECT * FROM {table_name} WHERE Probe == " + probe)
	# 	else:
	# 		probes = self.genesToProbes[probe]
	# 		sqlList = '(' + ', '.join(probes) + ')'
	# 		cols, rows = self.rawData.getTable(sqlCmd="SELECT * FROM {table_name} WHERE Probe IN " + sqlList)
	# 	# assert len(rows) == 1
	# 	groups = {}
	# 	for row in rows:
	# 		if isgene:
	# 			for col, el in zip(cols,row):
	# 				group = col.name.strip().strip('"').split('_')[0]
	# 				if group == 'Probe':
	# 					curProbe = el
	# 		for col, el in zip(cols,row):
	# 			group = col.name.strip().strip('"').split('_')[0]
	# 			if group != 'Probe':
	# 				if isgene:
	# 					group += '_' + curProbe
	# 				if group in groups:
	# 					groups[group].append(el)
	# 				else:
	# 					groups[group] = [el]

	# 	series = {}
	# 	for group, data in groups.items():
	# 		data = sorted(data)
	# 		dist = [
	# 					group,
	# 					min(data),
	# 					percentile(data,0.25),
	# 					percentile(data,0.5),
	# 					percentile(data,0.75),
	# 					max(data)
	# 				]
	# 		series[group] = dist
	# 	if isgene:
	# 		pconfig['groups'] = sorted(sorted(groups.keys()), key = lambda x: x.split('_')[1])
	# 	else:
	# 		pconfig['groups'] = sorted(groups.keys())


	# 	sseries = []
	# 	for group in pconfig['groups']:
	# 		sseries.append( series[group])

	# 	pdata = {probe:sseries}
	# 	# if not isgene:
	# 	#     pdata = {probe:series}
	# 	# else:
	# 	#     pdata = {}
	# 	#     for dist in series:
	# 	#         p = dist[0].split('_')[1]
	# 	#         if p not in pdata:
	# 	#             pdata[p] = [dist]
	# 	#         else:
	# 	#             pdata[p].append(dist)

	# 	# print(pdata)
	# 	return boxplot.plot(pdata,pconfig=pconfig)



	# def volcanoPlot(self):
	# 	cols, rows = self.diffExp.getTable(sqlCmd="SELECT gene, logFC, adj_P_Val FROM {table_name} ")

	# 	lava = {'not significant (rarefied)':[], 'significant':[]}
	# 	for gene, lfc, apv in rows:
	# 		if abs(lfc) > 0.5 and apv < 0.1:
	# 			lava['significant'].append({'name':gene, 'x':lfc, 'y':-math.log(apv,2)})
	# 		elif random() <  0.1: # rarify insignificant points so page loads faster 
	# 			lava['not significant (rarefied)'].append([lfc,-math.log(apv,2)])

	# 	return scatter.plot(lava, pconfig={'ylab':'Negative log of adjusted p value', 'xlab':'average log fold change', 'title':'Volcano Plot'})

	# def maPlot(self):
	# 	cols, rows = self.diffExp.getTable(sqlCmd="SELECT gene, logFC, adj_P_Val, AveExpr FROM {table_name} ")

	# 	lava = {'not significant (rarefied)':[], 'significant':[]}
	# 	for gene, lfc, apv, aE in rows:
	# 		if abs(lfc) > 0.5 and apv < 0.1:
	# 			lava['significant'].append({'name':gene, 'y':lfc, 'x':aE})
	# 		elif random() <  0.1: # rarify insignificant points so page loads faster 
	# 			lava['not significant (rarefied)'].append([aE,lfc])

	# 	return scatter.plot(lava, pconfig={
	# 								'ylab':'Ave. Log Fold Change', 
	# 								'xlab':'Ave. Expression', 
	# 								'title':'MA Plot'})

	# def parseRawDataTable(self, filename):
	# 	dt = SqlDataTable('raw_data')
	# 	with open(filename) as rD:
	# 		header = rD.readline()
	# 		for col in header.split('\t'):
	# 			col = '_'.join(col.strip().split('.'))
	# 			if 'ids' in col:
	# 				dt.addColumnInfo('Probe', 'TEXT')
	# 			else:
	# 				dt.addColumnInfo(col, 'FLOAT')
	# 		dt.initSqlTable()
	# 		rdr = csv.reader(rD,delimiter='\t')
	# 		dt.addManyRows(rdr)
	# 	return dt



	def getConditionsFromFilename(self,fname):
		conds = []
		for condition in self.conditions:
			if condition in fname:
				conds.append(condition)
		return conds
		Filename_does_not_contain_condition = False
		assert Filename_does_not_contain_condition

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


def openMaybeZip(fname):
	end = fname.split('.')[-1]
	if end == 'gz':
		return( gzip.open(fname))
	else:
		return( open(fname))



def split_over_columns(els, rowwise=False):
	"""
	Given a list of lists of strings containing html 
	split the strings into multiple html 'columns' using
	bootstraps framework.
	@parameter List of lists of strings. Each sub list is a column. Up to 12 columns.

	@return Valid html string.
	"""
	if not rowwise:
		ncols = len(els)
		assert ncols <= 12
		rows = []
		for sublist in els:
			for i, el in enumerate(sublist):
				if len(rows) <= i:
					rows.append([])
				rows[i].append(el)
	else:
		rows = els
		rowsizes = [len(row) for row in rows]
		ncols = max(rowsizes)
		assert ncols <= 12

	colsize = 12 / ncols

	outstr = """
			 """
	for i, row in enumerate(rows):
		outstr += """
					<div class="row">
				  """
		for j, el in enumerate(row):
			outstr += """
						<div class="col-md-{}">
							{}
						</div>
					  """.format(colsize,el)
		outstr += """
					</div>
				  """
	return outstr

