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

		self.parseTables()
		self.makeProbeGeneMaps()

		self.sections = []
		self.buildDiffExpTable()
		self.buildSigPlots()
		self.buildGeneBoxPlots()

	def parseTables(self):
		diffFiles = [dF for dF in self.find_log_files(config.sp['microarray']['diff_exp'])]
		print(diffFiles)
		assert len(diffFiles) == 1
		self.diffExp = self.parseDiffExpTable(diffFiles[0]['fn'])

		rawFiles = [rF for rF in self.find_log_files(config.sp['microarray']['raw_data'])]
		print(rawFiles)
		assert len(rawFiles) == 1
		self.rawData = self.parseRawDataTable(rawFiles[0]['fn'])

	def makeProbeGeneMaps(self):

		cols, rows = self.diffExp.getTable(sqlCmd= "SELECT Probe, gene FROM {table_name}")
		self.probeToGenes = {}
		self.genesToProbes = {}
		for probe, gene in rows:
			self.probeToGenes[probe] = gene
			if gene not in self.genesToProbes:
				self.genesToProbes[gene] = [probe]
			else:
				self.genesToProbes[gene].append(probe)

		def buildBetaDiversityCharts(self):
		plot = self.buildJSDChart()
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

		# Only calculate beta diversity from the highest resolution
		cols, rows = self.rawData.getTable()
		norm_sample = {sample:[] for sample in self.samples.values()}
		for row in rows:
			for i,col in enumerate(cols):
				if col.name == 'taxa':
					continue
				sName = '-'.join(col.name.split('_'))
				sample = self.samples[sName]
				norm_sample[sample].append(row[i])

		cSims = { sample : {sample:1 for sample in self.samples.values()} for sample in self.samples.values()}
		for s1, s2 in itertools.combinations(self.samples.values(),2):
			cos = Cos(norm_sample[s1], norm_sample[s2])
			cSims[s1][s2] = cos
			cSims[s2][s1] = cos

		plotData = []
		for condition, samples in self.conditions.items():
			coss = []
			for s1, s2 in itertools.combinations(samples,2):    
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

		for c1,c2 in itertools.combinations(self.conditions.keys(),2):
			samples1 = self.conditions[c1]
			samples2 = self.conditions[c2]
			coss = []
			for s1, s2 in itertools.combinations(samples1+samples2,2):
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

		pconfig = {'ylab':'Cosine Similarity', 'xlab':'Condition', 'title':'Beta Diversity', 'groups':self.conditions.keys()}
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

		# Only calculate beta diversity from the highest resolution
		cols, rows = self.rawData.getTable()
		norm_sample = {sample:[] for sample in self.samples.values()}
		for row in rows:
			for i,col in enumerate(cols):
				if col.name == 'taxa':
					continue
				sName = '-'.join(col.name.split('_'))
				sample = self.samples[sName]
				norm_sample[sample].append(row[i])

		jDists = { sample : {sample:1 for sample in self.samples.values()} for sample in self.samples.values()}
		for s1, s2 in itertools.combinations(self.samples.values(),2):
			jsd = JSD(norm_sample[s1], norm_sample[s2])
			jDists[s1][s2] = jsd
			jDists[s2][s1] = jsd

		plotData = []
		for condition, samples in self.conditions.items():
			jsds = []
			for s1, s2 in itertools.combinations(samples,2):    
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

		for c1,c2 in itertools.combinations(self.conditions.keys(),2):
			samples1 = self.conditions[c1]
			samples2 = self.conditions[c2]
			jsds = []
			for s1, s2 in itertools.combinations(samples1+samples2,2):
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

		pconfig = {'ylab':'Jensen-Shannon Distance', 'xlab':'Condition', 'title':'Beta Diversity', 'groups':self.conditions.keys()}
		bPlot = boxplot.plot({'beta_diversity':plotData},pconfig=pconfig)
		plot = "<p>The beta diversity (Jensen-Shannon Distance) across and between conditions</p>\n"
		plot += bPlot
		return plot


	def buildGeneBoxPlots(self):
		cols, rows = self.diffExp.getTable(sqlCmd="SELECT gene FROM {table_name}  WHERE adj_P_val < 0.1 AND logFC > 0.5")
		genes = {}
		for gene in rows:
			genes[gene] = True
		htmlRows = []
		rowSize = 2
		for i,gene in enumerate(genes.keys()):
			if i % rowSize == 0:
				htmlRows.append([""]*rowSize)
			gene = gene[0]
			htmlRows[i / rowSize][i % rowSize] = self.geneBoxPlot(gene,isgene=True)
		html_str = split_over_columns(htmlRows, rowwise=True)
		self.sections.append({
			'name' : 'Gene Expression Levels',
			'anchor' : 'gene_exp_lvls',
			'content' : html_str
			})

	def buildDiffExpTable(self):

		html_str = self.diffExp.as_html(sqlCmd="SELECT  * FROM {table_name} WHERE adj_P_Val < 0.005 AND AveExpr > 8")
		self.sections.append({
			'name' : 'Differential Expression',
			'anchor' : 'diff_exp',
			'content' : html_str
			})

	def buildSigPlots(self):
		volcs = self.volcanoPlot()
		mas = self.maPlot()
		html_str = split_over_columns([[volcs],[mas]])
		self.sections.append({
			'name' : 'Significance Plots',
			'anchor' : 'sig_plots',
			'content' : html_str
			})

	def geneBoxPlot(self, probe, isgene=False):
		pconfig = {'ylab':'Expression Level', 'xlab':'Condition', 'title':'{} Expression Levels'.format(probe)}
		if not isgene:
			cols, rows = self.rawData.getTable(sqlCmd="SELECT * FROM {table_name} WHERE Probe == " + probe)
		else:
			probes = self.genesToProbes[probe]
			sqlList = '(' + ', '.join(probes) + ')'
			cols, rows = self.rawData.getTable(sqlCmd="SELECT * FROM {table_name} WHERE Probe IN " + sqlList)
		# assert len(rows) == 1
		groups = {}
		for row in rows:
			if isgene:
				for col, el in zip(cols,row):
					group = col.name.strip().strip('"').split('_')[0]
					if group == 'Probe':
						curProbe = el
			for col, el in zip(cols,row):
				group = col.name.strip().strip('"').split('_')[0]
				if group != 'Probe':
					if isgene:
						group += '_' + curProbe
					if group in groups:
						groups[group].append(el)
					else:
						groups[group] = [el]

		series = {}
		for group, data in groups.items():
			data = sorted(data)
			dist = [
						group,
						min(data),
						percentile(data,0.25),
						percentile(data,0.5),
						percentile(data,0.75),
						max(data)
					]
			series[group] = dist
		if isgene:
			pconfig['groups'] = sorted(sorted(groups.keys()), key = lambda x: x.split('_')[1])
		else:
			pconfig['groups'] = sorted(groups.keys())


		sseries = []
		for group in pconfig['groups']:
			sseries.append( series[group])

		pdata = {probe:sseries}
		# if not isgene:
		#     pdata = {probe:series}
		# else:
		#     pdata = {}
		#     for dist in series:
		#         p = dist[0].split('_')[1]
		#         if p not in pdata:
		#             pdata[p] = [dist]
		#         else:
		#             pdata[p].append(dist)

		# print(pdata)
		return boxplot.plot(pdata,pconfig=pconfig)



	def volcanoPlot(self):
		cols, rows = self.diffExp.getTable(sqlCmd="SELECT gene, logFC, adj_P_Val FROM {table_name} ")

		lava = {'not significant (rarefied)':[], 'significant':[]}
		for gene, lfc, apv in rows:
			if abs(lfc) > 0.5 and apv < 0.1:
				lava['significant'].append({'name':gene, 'x':lfc, 'y':-math.log(apv,2)})
			elif random() <  0.1: # rarify insignificant points so page loads faster 
				lava['not significant (rarefied)'].append([lfc,-math.log(apv,2)])

		return scatter.plot(lava, pconfig={'ylab':'Negative log of adjusted p value', 'xlab':'average log fold change', 'title':'Volcano Plot'})

	def maPlot(self):
		cols, rows = self.diffExp.getTable(sqlCmd="SELECT gene, logFC, adj_P_Val, AveExpr FROM {table_name} ")

		lava = {'not significant (rarefied)':[], 'significant':[]}
		for gene, lfc, apv, aE in rows:
			if abs(lfc) > 0.5 and apv < 0.1:
				lava['significant'].append({'name':gene, 'y':lfc, 'x':aE})
			elif random() <  0.1: # rarify insignificant points so page loads faster 
				lava['not significant (rarefied)'].append([aE,lfc])

		return scatter.plot(lava, pconfig={
									'ylab':'Ave. Log Fold Change', 
									'xlab':'Ave. Expression', 
									'title':'MA Plot'})

	def parseRawDataTable(self, filename):
		dt = SqlDataTable('raw_data')
		with open(filename) as rD:
			header = rD.readline()
			for col in header.split('\t'):
				col = '_'.join(col.strip().split('.'))
				if 'ids' in col:
					dt.addColumnInfo('Probe', 'TEXT')
				else:
					dt.addColumnInfo(col, 'FLOAT')
			dt.initSqlTable()
			rdr = csv.reader(rD,delimiter='\t')
			dt.addManyRows(rdr)
		return dt


	def parseDiffExpTable(self,filename):
		dt = SqlDataTable('diff_exp')
		dt.addColumnInfo('Probe','TEXT')
		dt.addColumnInfo('logFC','FLOAT')
		dt.addColumnInfo('AveExpr','FLOAT')
		dt.addColumnInfo('t','FLOAT')
		dt.addColumnInfo('P_Value','FLOAT')
		dt.addColumnInfo('adj_P_Val','FLOAT')
		dt.addColumnInfo('B','FLOAT')
		dt.addColumnInfo('gene','TEXT')
		dt.initSqlTable()
		with open(filename) as dE:
			dE.readline()
			rdr = csv.reader(dE,delimiter='\t')
			dt.addManyRows(rdr)
		return dt




def percentile(N, percent, key=lambda x:x):
	"""
	Find the percentile of a list of values.

	@parameter N - is a list of values. Note N MUST BE already sorted.
	@parameter percent - a float value from 0.0 to 1.0.
	@parameter key - optional key function to compute value from each element of N.

	@return - the percentile of the values
	"""
	if not N:
		return None
	k = (len(N)-1) * percent
	f = math.floor(k)
	c = math.ceil(k)
	if f == c:
		return key(N[int(k)])
	d0 = key(N[int(f)]) * (c-k)
	d1 = key(N[int(c)]) * (k-f)
	return d0+d1

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



