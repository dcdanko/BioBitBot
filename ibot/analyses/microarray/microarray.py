#!/usr/bin/env python

""" IBot analysis to parse output from CGAT Microarray Differential Expression Pipeline"""

from ibot.utils.utils import *
import yaml
import traceback
from collections import OrderedDict
import logging
import re
import csv
from ibot import config
from ibot.utils.errors import *
from ibot.analyses.base_analysis import BaseIBotAnalysis
from ibot.plots.sql_data_table import SqlDataTable
import ibot.plots.scatterplot as scatter
import ibot.plots.boxplot as boxplot
from ibot.modules import distance, significance, pca
import math
from random import random
# Initialise the logger
logger = logging.getLogger(__name__)


class IBotAnalysis(BaseIBotAnalysis):

	def __init__(self):
		print('a')
		# Initialise the parent object
		super(IBotAnalysis, self).__init__(
												name='Microarray Analysis', 
												anchor='microarray',  
												info="Displays the results of differential expression analysis on a microarray"
											)

		try:
			self.setMetadata()
			self.parseDataFiles()
			self.makeProbeGeneMaps()
		except Exception as e:
			logger.error("Couldn't parse files for microarray analysis")
			print(e)
			raise( e)

		try:
			distMod = distance.IBotModule()
			distMod.buildChartSet(self.norm_table,self.conditions)
			self.modules.append(distMod)
		except Exception as e:
			logger.error("The distance module broke in microarray analysis")
			print(traceback.format_exc(e))

		# pcaMod = pca.IBotModule()
		# pcaMod.buildChartSet(ptsfilename,vefilename,self.conditions)
		# self.modules.append(pcaMod)
		try:
			sigMod = significance.IBotModule()
			for table in self.diff_exp_tables:
				groups = getConditionsFromName(table.name,self.conditions)
				sigMod.buildChartSet(table.name,table,idcol='gene',groups=groups,strict=2)
			self.modules.append(sigMod)
		except Exception as e:
			logger.error("The significance module broke in microarray analysis")
			print(traceback.format_exc(e))


	def setMetadata(self):
		metaF = [f for f in self.find_log_files(config.sp['uarray']['metadata'])]
		if len(metaF) != 1:
			raise IBotMetadataError(len(metaF))
		with openMaybeZip(metaF[0]['fn']) as mF:
			metadata = yaml.load(mF)
			conditions = metadata['conditions']
			self.conditions = sorted(conditions,key=len,reverse=True)

	def parseDataFiles(self):
		# Differential Expression Tables
		diff_exp_files = [f for f in self.find_log_files(config.sp['uarray']['diff_exp'])]
		self.diff_exp_tables = [parseDiffExpTable(f['fn']) for f in diff_exp_files]

		# Normalised Expression Table
		tName = "norm_exp"
		dt = SqlDataTable(tName)
		norm_file = [f for f in self.find_log_files(config.sp['uarray']['norm_exp'])]
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
		probemap = [f for f in self.find_log_files(config.sp['uarray']['probemap'])]
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


def getConditionsFromName(name,conditions):
	conds = []
	for condition in conditions:
		if condition.lower() in name.lower():
			conds.append(condition)
	if len(conds) > 0:
		return conds
	Filename_does_not_contain_condition = True
	if Filename_does_not_contain_condition:
		print(name)
		assert(False)




