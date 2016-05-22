#!/usr/bin/env python

"""
Compare Metagenomic WGS samples
Based on the CGAT metagenome communities pipeline.
"""

from ibot.plots.sql_data_table import SqlDataTable
from collections import OrderedDict
from tree import Tree, TreeNode
from ibot.utils.utils import *
import logging
import re

from ibot import config, plots
from ibot.analyses.base_analysis import BaseIBotAnalysis
import ibot.plots.boxplot as boxplot
import ibot.plots.scatterplot as scatter
import ibot.plots.treemap as treemap
import math
from ibot.modules import distance, significance, pca, phylogeny, alpha_diversity, alignment_stats_ubiome
from random import random
import gzip
import itertools
import yaml
import traceback
# Initialise the logger
logger = logging.getLogger(__name__)




class IBotAnalysis(BaseIBotAnalysis):

	def __init__(self):

		# Initialise the parent object
		super(IBotAnalysis, self).__init__(
					name='Microbiome Analysis', 
					anchor='microbiome', 
					info="Differential Analysis of Microbiomes")

		try:
			self.setMetadata()
		except Exception as e:
			logger.error("Couldn't parse critical files for microbiome analysis. Quitting.")
			logger.error(traceback.format_exc(e))
			raise(e)
		
		# Experiment Overview
		try:
			overviewFiles = [f['fn'] for f in self.find_log_files['ubiome']['overview']]
			assert len(overviewFiles) == 1
			with open(overviewFiles[0]) as oF:
				overview = oF.read()
				overviewMod = markdown.IBotModule(name='Experiment Overview')
				overviewMod.buildChartSet(overview)
				self.modules.append(overviewMod)
		except Exception as e:
			logger.error("The markdown module broke in microbiome analysis.")
			logger.error(traceback.format_exc(e))

		# Alignment Stats Charts
		try:
			self.parseCountFiles()
			self.parseTreeFiles()
			self.buildPhylogenyTree()
			self.populateTreeSeqCounts()
			self.parseAlignmentStatFiles()
			astats = alignment_stats_ubiome.IBotModule()
			astats.buildChartSet(self.taxa_hierarchy, self.phylo_tree, self.samples, self.alignment_stat_files)
			self.modules.append(astats)
		except Exception as e:
			logger.error("The alignment stats module broke in microbiome analysis.")
			logger.error(traceback.format_exc(e))

		# Alpha Diversity Charts
		try:
			self.parseDiversityFiles()
			adiv = alpha_diversity.IBotModule()
			adiv.buildChartSet(self.conditions, self.samples, self.diversity_files, self.taxa_hierarchy)
			self.modules.append(adiv)
		except Exception as e:
			logger.error("The alpha diversity module broke in microbiome analysis.")
			logger.error(traceback.format_exc(e))

		# Beta Diversity Charts
		try:
			self.parseNormCountTables()
			distMod = distance.IBotModule()
			lowestTaxa = self.taxa_hierarchy[-1]
			lowestCounts = self.norm_count_tables[lowestTaxa]
			distMod.buildChartSet(lowestCounts,self.conditions.keys(),idcol='taxa')
			self.modules.append(distMod)
		except Exception as e:
			logger.error("The distance module broke in microbiome analysis.")
			logger.error(traceback.format_exc(e))

		# PCA Charts
		try:
			pcaMod = pca.IBotModule()
			pts = [f for f in self.find_log_files( config.sp['ubiome']['pca']['bacteria']['points'])]
			pts = pts[0]['fn']
			ve = [f for f in self.find_log_files( config.sp['ubiome']['pca']['bacteria']['variance'])]
			ve = ve[0]['fn']
			pcaMod.buildChartSet(pts,ve,self.conditions)
			self.modules.append(pcaMod)
		except Exception as e:
			logger.error("The pca module broke in microbiome analysis.")
			logger.error(traceback.format_exc(e))

		# Significance Charts
		try:
			self.parseDiffCountTables()
			sigMod = significance.IBotModule()
			for taxa in self.taxa_hierarchy[::-1]:
				table = self.diff_count_tables[taxa]
				sigMod.buildChartSet(taxa.title(),table,idcol='taxa',groups=None,strict=2)
			self.modules.append(sigMod)
		except Exception as e:
			logger.error("The significance module broke in microbiome analysis")
			logger.error(traceback.format_exc(e))
		
		# Phylogeny Tree-Maps 
		try:
			self.parseTreeFiles()
			self.buildPhylogenyTree()
			self.populateTreeSeqCounts()
			self.populateTreeNormCounts()
			treeMod = phylogeny.IBotModule()
			treeMod.buildChartSet(self.conditions,self.phylo_tree, self.taxa_hierarchy, self.root_offset)
			self.modules.append(treeMod)
		except Exception as e:
			logger.error("The phylogeny tree module broke in microbiome analysis")
			logger.error(traceback.format_exc(e))
		
	def setMetadata(self):
		metaF = [f for f in self.find_log_files(config.sp['ubiome']['metadata'])]
		assert len(metaF) == 1
		with open(metaF[0]['fn']) as mF:
			metadata = yaml.load(mF)
			samples = metadata['samples']
			self.root_offset = int(metadata['taxa_offset'])
			self.taxa_hierarchy = metadata['taxa_hierarchy']
			self.additional_taxa = metadata['other_taxa']
			self.aligner = metadata['aligner']
			self.conditions = {}
			self.samples = {}
			for sampleName in samples:
				condition = sampleName.split('-')[1]
				self.samples[sampleName] = Sample(sampleName,condition)
				if condition not in self.conditions:
					self.conditions[condition] = []
				self.conditions[condition].append( self.samples[sampleName])

	def parseCountFiles(self):
		countFiles = self.find_log_files( config.sp['ubiome']['raw_count']['taxa'])
		self.countFiles = [f for f in countFiles if self.aligner in f['fn']]
		assert len(self.countFiles) == len(self.taxa_hierarchy)*len(self.samples)

	def parseAlignmentStatFiles(self):
		alignment_stat_files = [f for f in self.find_log_files( config.sp['ubiome']['align_stats']['gene'])]
		alignment_stat_files += [f for f in self.find_log_files( config.sp['ubiome']['align_stats']['taxa'])]
		self.alignment_stat_files = [f for f in alignment_stat_files if self.aligner in f['fn']]
		assert len(self.alignment_stat_files) == (len(self.taxa_hierarchy)+len(self.additional_taxa))*len(self.samples)

	def parseDiversityFiles(self):
		diversity_files = [f for f in self.find_log_files( config.sp['ubiome']['alpha_diversity']['gene'])]
		diversity_files += [f for f in self.find_log_files( config.sp['ubiome']['alpha_diversity']['taxa'])]
		diversity_files = [f for f in diversity_files if 'other' not in f['fn']]
		self.diversity_files = [f for f in diversity_files if self.aligner in f['fn']]
		assert len(self.diversity_files) == len(self.taxa_hierarchy)

	def parseDiffCountTables(self):
		diff_count_files = [f for f in self.find_log_files( config.sp['ubiome']['diff_count']['all'])]
		diff_count_files = [f for f in diff_count_files if self.aligner in f['fn']]
		diff_count_files = [f for f in diff_count_files if 'other' not in f['fn']]
		assert len(diff_count_files) == len(self.taxa_hierarchy)
		self.diff_count_tables = { self.getTaxaFromFilename(f['fn']) : parseDiffExpTable(f['fn']) for f in diff_count_files}

	def parseNormCountTables(self):
		self.norm_count_tables = {}
		for f in self.find_log_files(config.sp['ubiome']['norm_count']['taxa']):
			fn = f['fn']
			taxa = self.getTaxaFromFilename(fn)
			tName = "{}_norm_count".format(taxa)
			dt = SqlDataTable(tName)
			with open(fn) as nF:
				header = nF.readline()
				header = [head.strip() for head in header.split()]
				header = ['_'.join(head.split('.')) for head in header]
				
				for head in header:
					head = head.strip('"')
					if '_count' in head:
						head = head[:-6]

					head = head.strip().strip('"')
					if head == "taxa":
						dt.addColumnInfo(head,"TEXT")
					else:
						dt.addColumnInfo(head,"FLOAT")	

				dt.initSqlTable()
				rdr = csv.reader(nF,delimiter='\t')
				dt.addManyRows(rdr)
			self.norm_count_tables[taxa] = dt
			
	def parseTreeFiles(self):
		treeF = [f for f in self.find_log_files(config.sp['ubiome']['taxa_tree'])]
		assert len(treeF) == 1
		self.treeF = treeF[0]

	def buildPhylogenyTree(self):
		if hasattr(self,'phylo_tree'):
			return
		treeF = self.treeF
		phyloRoot = TreeNode('ROOT', None)
		with openMaybeZip(treeF['fn']) as tF:
			header = tF.readline()
			for line in tF:
				hierarchy = line.split('\t')
				assert len(hierarchy) == 7
				rParent = phyloRoot
				for i, taxon in enumerate(hierarchy):
					rParent = rParent.addNameIfNotPresent(taxon.strip())

		self.phylo_tree = Tree(phyloRoot, self.taxa_hierarchy)

	def populateTreeSeqCounts(self):
		if hasattr(self,'tree_seq_counts_populated'):
			return
		for countF in self.countFiles:
			with openMaybeZip(countF['fn']) as cF:
				cF.readline()
				sample = self.getSampleFromFilename(countF['fn'])
				for line in cF:
					name, count = line.split()
					count = int(count)
	
					self.phylo_tree.all_nodes[name].seqCountsBySamples[sample] = count

		# We can miss samples if the taxa isn't present 
		for node in self.phylo_tree:
			for sample in self.samples.values():
				if sample not in node.seqCountsBySamples:
	
					node.seqCountsBySamples[sample] = 0

		for node in self.phylo_tree:
			node.findSeqCountsThatDidNotAlignToChildren()
		self.tree_seq_counts_populated = True

	def populateTreeNormCounts(self):
		if hasattr(self,'tree_norm_counts_populated'):
			return
		for taxaRank, norm_table in self.norm_count_tables.items():
			sqlCmd = "SELECT * FROM {table_name} "
			cols, rows = norm_table.getTable(sqlCmd=sqlCmd)
			for row in rows:
				vals = row[:-1]
				taxa = row[-1]
				for col,val in zip(cols,vals):
					sample = self.samples['-'.join(col.name.split('_'))]
					self.phylo_tree.all_nodes[taxa].normCountsBySamples[sample] = val


		# We can miss samples if the taxa isn't present 
		for node in self.phylo_tree:
			for sample in self.samples.values():
				if sample not in node.normCountsBySamples:
	
					node.normCountsBySamples[sample] = 0.000001 # pseudocount
		self.tree_norm_counts_populated = True

	def getTaxaFromFilename(self,fname):
		for taxa in self.taxa_hierarchy:
			if taxa in fname:
				return taxa
		if 'gene' in fname:
			return 'gene'
		Filename_does_not_contain_taxa = False
		assert Filename_does_not_contain_taxa

	def getSampleFromFilename(self,fname):
		for sample in self.samples.values():
			if sample.name in fname:

				return sample
		Filename_does_not_contain_sample = False
		assert Filename_does_not_contain_sample




class Sample(object):

	def __init__(self,name,condition):
		self.name = name
		self.condition = condition

	def __str__(self):
		return "Sample: {}".format(self.name)




