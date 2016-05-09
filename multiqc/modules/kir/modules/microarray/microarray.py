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
import yaml
import itertools


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
		self.buildBetaDiversityCharts()
		self.buildPCACharts()
		self.buildSignifPlots()

	def setMetadata(self):
		metaF = [f for f in self.find_log_files(config.sp['microarray']['metadata'])]
		assert len(metaF) == 1
		with openMaybeZip(metaF[0]['fn']) as mF:
			metadata = yaml.load(mF)
			self.conditions = metadata['conditions']

	def parseDataFiles(self):
		# Differential Expression Tables
		diff_exp_files = [f for f in self.find_log_files(config.sp['microarray']['diff_exp'])]
		self.diff_exp_tables = [parseDiffExpTable(f['fn']) for f in diff_exp_files]

		# Normalised Expression Table
		tName = "norm_exp"
		dt = SqlDataTable(tName)
		norm_file = [f for f in self.find_log_files(config.sp['microarray']['norm_exp'])]
		with openMaybeZip(norm_file[0]['fn']) as nF:
			header = nF.readline()
			header = [head.strip() for head in header.split()]
			header = ['_'.join(head.split('.')) for head in header]
			for head in header:
				head = head.strip('"')
				if head == "ids":
					dt.addColumnInfo(head,"TEXT")
				else:
					dt.addColumnInfo(head,"FLOAT")	

			dt.initSqlTable()
			rdr = csv.reader(nF,delimiter='\t')
			dt.addManyRows(rdr)
		self.norm_table = dt


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


		pts = [f for f in self.find_log_files( config.sp['microarray']['pca']['points'])]
		pts = pts[0]['fn']
		points = {}
		with open(pts) as pF:
			pF.readline()
			for line in pF:
				line = line.split()
				# print(line)
				condition = self.getConditionsFromFilename('-'.join(line[0].strip().split('.')))[0]
				vals = [float(pt) for pt in line[1:]]
				if condition not in points:
					points[condition] = []
				points[condition].append(vals[:axes_interest])

		ve = [f for f in self.find_log_files( config.sp['microarray']['pca']['variance'])]
		ve = ve [0]['fn']
		with open(ve) as vF:
			vF.readline()
			axes = []
			for line in vF:
				line = line.split()
				val = float(line[1].strip())
				axes.append(val)
			axes = axes[:axes_interest]

		plotDatasets = OrderedDict()
		for i,j in itertools.combinations(range(axes_interest),2):
			plotData = {}
			for condition in self.conditions:
				plotData[condition] = []
				for sample in points[condition]:
					x = sample[i]
					y = sample[j]
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


	def buildSignifPlots(self):

		def oneVolcanoPlot(table,conditions,minLfc=0.75,maxApv=0.05,rarefier=0.1):
			cols, rows = table.getTable(sqlCmd="SELECT gene, logFC, adj_P_Val FROM {table_name} ")


			lava = {'not significant (rarefied)':[], 'significant':[]}
			for gene, lfc, apv in rows:
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

		def oneMaPlot(table,conditions,minLfc=0.75,maxApv=0.05,rarefier=0.1):
			cols, rows = table.getTable(sqlCmd="SELECT gene, logFC, adj_P_Val, AveExpr FROM {table_name} ")

			lava = {'not significant (rarefied)':[], 'significant':[]}
			for  gene, lfc, apv, aE in rows:
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
		for diff_exp_table in self.diff_exp_tables:
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

	def buildBetaDiversityCharts(self):
		print(self.conditions)
		plot = ''
		plot += self.buildJSDChart()
		plot += self.buildCosChart()
		self.sections.append({
			'name' : 'Beta Diversity',
			'anchor' : 'beta_diversity',
			'content' : plot
			})

	def buildCosChart(self):

		def Cos(A,B):
			assert len(A) == len(B)
			magA = math.sqrt( sum([el*el for el in A]))
			magB = math.sqrt( sum([el*el for el in B]))
			dot = 0.0
			for a,b in zip(A,B):
				dot += a*b

			return dot/(magA*magB)	


		cols, rows = self.norm_table.getTable()
		samples = [col.name for col in cols if 'ids' not in col.name]
		norm_sample = {sample:[] for sample in samples}
		for row in rows:
			for i,col in enumerate(cols):
				if col.name == 'ids':
					continue
				norm_sample[col.name].append(row[i])

		cSims = { sample : {sample:1 for sample in samples} for sample in samples}
		for s1, s2 in itertools.combinations(samples,2):
			cos = Cos(norm_sample[s1], norm_sample[s2])
			cSims[s1][s2] = cos
			cSims[s2][s1] = cos

		plotData = []
		for condition in self.conditions:
			matchingSamples = []
			for sample in samples:
				if condition in self.getConditionsFromFilename(sample):
					matchingSamples.append(sample)
			coss = []
			for s1, s2 in itertools.combinations(matchingSamples,2):	
				coss.append( cSims[s1][s2])
			dist = [
						"{}".format(condition),
						min(coss),
						percentile(coss,0.25),
						percentile(coss,0.5),
						percentile(coss,0.75),
						max(coss)
					]
			plotData.append(dist)

		for c1,c2 in itertools.combinations(self.conditions,2):
			matchingSamples1 = []
			for sample in samples:
				if c1 in self.getConditionsFromFilename(sample):
					matchingSamples1.append(sample)
			matchingSamples2 = []
			for sample in samples:
				if c2 in self.getConditionsFromFilename(sample):
					matchingSamples2.append(sample)
			coss = []
			for s1 in matchingSamples1:
				for s2 in matchingSamples2:
					coss.append( cSims[s1][s2])
			dist = [
						"{} {}".format(c1,c2),
						min(coss),
						percentile(coss,0.25),
						percentile(coss,0.5),
						percentile(coss,0.75),
						max(coss)
					]
			plotData.append(dist)

		pconfig = {'ylab':'Cosine Similarity', 'xlab':'Condition', 'title':'Beta Diversity', 'groups':self.conditions}
		bPlot = boxplot.plot({'beta_diversity':plotData},pconfig=pconfig)
		plot = "<p>The beta diversity (Cosine Similarity) across and between conditions</p>\n"
		plot += bPlot
		return plot

	def buildJSDChart(self):

		def JSD(P,Q):
			assert len(P) == len(Q)
			Psum = sum(P)
			P = [p/Psum for p in P]
			Qsum = sum(Q)
			Q = [q/Qsum for q in Q]
			def KLD(P,Q):
				ac = 0
				for i in range(len(P)):
					p = P[i] + 0.000001
					q = Q[i] + 0.000001
					ac += p * math.log(p/q)
				return ac
			M = [0]*len(P)
			for i in range(len(P)):
				p = P[i] 
				q = Q[i]
				M[i] = 0.5*(p+q)
			return math.sqrt(0.5*KLD(P,M) + 0.5*KLD(Q,M))	

		cols, rows = self.norm_table.getTable()
		samples = [col.name for col in cols if 'ids' not in col.name]
		norm_sample = {sample:[] for sample in samples}
		for row in rows:
			for i,col in enumerate(cols):
				if col.name == 'ids':
					continue
				norm_sample[col.name].append(row[i])

		jDists = { sample : {sample:1 for sample in samples} for sample in samples}
		for s1, s2 in itertools.combinations(samples,2):
			jsd = JSD(norm_sample[s1], norm_sample[s2])
			jDists[s1][s2] = jsd
			jDists[s2][s1] = jsd

		plotData = []
		for condition in self.conditions:
			matchingSamples = []
			for sample in samples:
				if condition in self.getConditionsFromFilename(sample):
					matchingSamples.append(sample)
			jsds = []
			for s1, s2 in itertools.combinations(matchingSamples,2):	
				jsds.append( jDists[s1][s2])
			dist = [
						"{}".format(condition),
						min(jsds),
						percentile(jsds,0.25),
						percentile(jsds,0.5),
						percentile(jsds,0.75),
						max(jsds)
					]
			plotData.append(dist)

		for c1,c2 in itertools.combinations(self.conditions,2):
			matchingSamples1 = []
			for sample in samples:
				if c1 in self.getConditionsFromFilename(sample):
					matchingSamples1.append(sample)
			matchingSamples2 = []
			for sample in samples:
				if c2 in self.getConditionsFromFilename(sample):
					matchingSamples2.append(sample)
			jsds = []
			for s1 in matchingSamples1:
				for s2 in matchingSamples2:
					jsds.append( jDists[s1][s2])
			dist = [
						"{} {}".format(c1,c2),
						min(jsds),
						percentile(jsds,0.25),
						percentile(jsds,0.5),
						percentile(jsds,0.75),
						max(jsds)
					]
			plotData.append(dist)

		pconfig = {'ylab':'Jensen-Shannon Distance', 'xlab':'Condition', 'title':'Beta Diversity', 'groups':self.conditions}
		bPlot = boxplot.plot({'beta_diversity':plotData},pconfig=pconfig)
		plot = "<p>The beta diversity (Jensen-Shannon Distance) across and between conditions</p>\n"
		plot += bPlot
		return plot


	def getConditionsFromFilename(self,fname):
		conds = []
		for condition in self.conditions:
			if condition.lower() in fname.lower():
				conds.append(condition)
		if len(conds) > 0:
			return conds
		Filename_does_not_contain_condition = True
		if Filename_does_not_contain_condition:
			print(fname)
			assert(False)


def parseDiffExpTable(filename):
	tName = filename.split('/')[-1]
	tName = tName.split('.')[0]
	tName = '_'.join(tName.split('-'))
	dt = SqlDataTable(tName)
	with open(filename) as dE:
		header = dE.readline().split()
		if len(header) == 8:
			dt.addColumnInfo('Probe','TEXT')
			dt.addColumnInfo('logFC','FLOAT')
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

