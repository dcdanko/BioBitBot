#!/usr/bin/env python

"""
Compare Metagenomic WGS samples
Based on the CGAT metagenome communities pipeline.
"""

from multiqc.plots.sql_data_table import SqlDataTable
from collections import OrderedDict
import logging
import re
import csv
from multiqc import config, BaseMultiqcModule, plots
import multiqc.plots.boxplot as boxplot
import multiqc.plots.scatterplot as scatter
import multiqc.plots.treemap as treemap
import math
from random import random
import gzip
import itertools
import yaml
# Initialise the logger
log = logging.getLogger(__name__)




class MultiqcModule(BaseMultiqcModule):

	def __init__(self):

		# Initialise the parent object
		super(MultiqcModule, self).__init__(name='Metagenomic Analysis', anchor='metagenome', 
		info="Compares metagenomic WGS experiments")

		self.setMetadata()
        self.parseDataFiles()
		self.buildPhylogenyTree()
		self.populateTreeSeqCounts()


		
		
		self.parseNormCountTables()
		self.populateTreeNormCounts()

		self.sections = []
		self.buildAlignmentStatsChart()
		self.buildAlphaDiversityCharts()
		self.buildBetaDiversityCharts()
		self.buildPCACharts()
		self.buildSignifPlots()
		self.buildRichnessCharts()
		self.buildPhylogenyTreeMaps()

	def parseNormCountTables(self):
		self.norm_count_tables = {}
		for f in self.find_log_files(config.sp['metagenomics']['norm_count']['taxa']):
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

        def setMetadata(self):
                metaF = [f for f in self.find_log_files(config.sp['metagenomics']['metadata'])]
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
                
                
        def parseDataFiles(self):
                alignment_stat_files = [f for f in self.find_log_files( config.sp['metagenomics']['align_stats']['gene'])]
		alignment_stat_files += [f for f in self.find_log_files( config.sp['metagenomics']['align_stats']['taxa'])]
                self.alignment_stat_files = [f for f in alignment_stat_files if self.aligner in f['fn']]
                assert len(self.alignment_stat_files) == (len(self.taxa_hierarchy)+len(self.additional_taxa))*len(self.samples)
		diversity_files = [f for f in self.find_log_files( config.sp['metagenomics']['alpha_diversity']['gene'])]
		diversity_files += [f for f in self.find_log_files( config.sp['metagenomics']['alpha_diversity']['taxa'])]
                self.diversity_files = [f for f in diversity_files if self.aligner in f['fn']]
                assert len(self.diversity_files) == len(self.taxa_hierarchy)
                
		diff_count_files = [f for f in self.find_log_files( config.sp['metagenomics']['diff_count']['gene'])]
		diff_count_files += [f for f in self.find_log_files( config.sp['metagenomics']['diff_count']['taxa'])]
                diff_count_files = [f for f in diff_count_files if self.aligner in f['fn']]
                assert len(diff_count_files) == len(self.samples)
                self.diff_count_tables = { self.getTaxaFromFilename(f['fn']) : parseDiffExpTable(f['fn']) for f in diff_count_files}

                treeF = [f for f in self.find_log_files(config.sp['metagenomics']['taxa_tree'])]
                assert len(treeF) == 1
                self.treeF = treeF[0]
                
                countFiles = self.find_log_files( config.sp['metagenomics']['raw_count']['taxa'])
                self.countFiles = [f for f in countFiles if self.aligner in f['fn']]
                assert len(self.countFiles) == len(self.taxa_hierarchy)*len(self.samples)
                
             

	def buildPhylogenyTree(self):
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

	def populateTreeNormCounts(self):
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


class Sample(object):

	def __init__(self,name,condition):
		self.name = name
		self.condition = condition

	def __str__(self):
		return "Sample: {}".format(self.name)

def openMaybeZip(fname):
	end = fname.split('.')[-1]
	if end == 'gz':
		return( gzip.open(fname))
	else:
		return( open(fname))


