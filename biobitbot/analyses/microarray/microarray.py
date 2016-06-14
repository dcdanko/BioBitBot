#!/usr/bin/env python

""" IBot analysis to parse output from CGAT Microarray Differential Expression Pipeline"""

from biobitbot.utils.utils import *
import yaml
import traceback
from collections import OrderedDict
import logging
import re
import csv
from biobitbot import config
from biobitbot.utils.errors import *
from biobitbot.analyses.base_analysis import BaseIBotAnalysis
from biobitbot.plots.sql_data_table import SqlDataTable
import biobitbot.plots.scatterplot as scatter
import biobitbot.plots.boxplot as boxplot
from biobitbot.modules import markdown, distance, significance, pca
import math
from random import random
# Initialise the logger
logger = logging.getLogger(__name__)


class IBotAnalysis(BaseIBotAnalysis):

	def __init__(self):
		# Initialise the parent object
		super(IBotAnalysis, self).__init__(
												name='Microarray Analysis', 
												anchor='microarray',  
												info="Displays the results of differential expression analysis on a microarray"
											)

		try:
			self.setMetadata()
                        titleMD = "####{}\n####Microarray - {}".format(self.description.title(), self.subtype.title())
                        titleMod = markdown.IBotModule(name=self.name.title())
			titleMod.buildChartSet(titleMD)
			self.modules.append(titleMod)
			self.makeProbeGeneMaps()
		except Exception as e:
			logger.error("Couldn't parse critical files for microarray analysis. Quitting.")
			logger.error(traceback.format_exc(e))
			raise(e)

		# Experiment Overview
		try:
			overviewFiles = [f for f in self.find_log_files(config.sp['uarray']['overview'])]
			assert len(overviewFiles) == 1
			with open(overviewFiles[0]['fn']) as oF:
				overview = oF.read()
				overviewMod = markdown.IBotModule(name='Experiment Overview')
				overviewMod.buildChartSet(overview)
				self.modules.append(overviewMod)
		except Exception as e:
			logger.error("The markdown module broke in microarray analysis.")
			logger.error(traceback.format_exc(e))

		try:
			self.parseNormExpTable()
			distMod = distance.IBotModule()
			distMod.buildChartSet(self.norm_table,self.conditions)
			self.modules.append(distMod)
		except Exception as e:
			logger.error("The distance module broke in microarray analysis")
			logger.error(traceback.format_exc(e))

		try:
			pcaMod = pca.IBotModule()
			pts = [f for f in self.find_log_files( config.sp['uarray']['pca']['points'])]
			pts = pts[0]['fn']
			ve = [f for f in self.find_log_files( config.sp['uarray']['pca']['variance'])]
			ve = ve [0]['fn']
			pcaMod.buildChartSet(pts,ve,self.conditions)
			self.modules.append(pcaMod)
		except Exception as e:
			logger.error("The pca module broke in microarray analysis")
			logger.error(traceback.format_exc(e))

		try:
			self.parseDiffExpTables()
			sigMod = significance.IBotModule()
			for table in self.diff_exp_tables:
                                print(table.name)
                                print(self.conditions)
				groups = table.name.split('_')
                                print(groups)
                                sigMod.buildChartSet(table.name,table,idcol='gene',groups=groups,strict=2)
			self.modules.append(sigMod)
		except Exception as e:
			logger.error("The significance module broke in microarray analysis")
			logger.error(traceback.format_exc(e))


	def setMetadata(self):
		metaF = [f for f in self.find_log_files(config.sp['uarray']['metadata'])]
		if len(metaF) != 1:
			raise IBotMetadataError(len(metaF))
		with openMaybeZip(metaF[0]['fn']) as mF:
			metadata = yaml.load(mF)
			conditions = metadata['conditions']
			self.conditions = sorted(conditions,key=len,reverse=True)
                        self.name = metadata['name']
                        if 'description' in metadata:
                                self.description = metadata['description']
                        else:
                                self.description = ''
                        if 'subtype' in metadata:
                                self.subtype = metadata['subtype']
                        else:
                                self.subtype = ''

	def parseNormExpTable(self):
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

	def parseDiffExpTables(self):
		diff_exp_files = [f for f in self.find_log_files(config.sp['uarray']['diff_exp'])]
		self.diff_exp_tables = []

		for f in diff_exp_files:
			fname = f['fn']
			try:		
				dET = parseDiffExpTable(fname)
				self.diff_exp_tables.append(dET)
			except Exception as e:
				logger.error("Failed to parse {} into diff exp table".format(fname))
				logger.error(traceback.format_exc(e))


	def makeProbeGeneMaps(self):
		probemap = [f for f in self.find_log_files(config.sp['uarray']['probemap'])]
		assert len(probemap) == 1
		with openMaybeZip(probemap[0]['fn']) as pM:
			pM.readline()
			self.probeToGenes = {}
			self.genesToProbes = {}
			for line in pM:
				probe, gene = [el.strip().strip('"') for el in line.split()][:2]
				self.probeToGenes[probe] = gene
				if gene not in self.genesToProbes:
					self.genesToProbes[gene] = [probe]
				else:
					self.genesToProbes[gene].append(probe)


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




