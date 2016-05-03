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
                
                
#        def setTaxaHierarchy(self):
#		taxaHierF  = [f for f in self.find_log_files(config.sp['metagenomics']['taxa_hier'])]
#		assert len(taxaHierF) == 1
#		taxaHierF = taxaHierF[0]
#		self.taxa_hierarchy = []
#		self.additional_taxa = []
#		with openMaybeZip(taxaHierF['fn']) as tHF:
#			self.root_offset = int(tHF.readline())
#			hierarchy = True
#			for line in tHF:
#				if line.strip() == '-':
#					hierarchy = False
#				elif hierarchy:
#					self.taxa_hierarchy.append(line.strip())
#				else:
#					self.additional_taxa.append(line.strip())
#
#	def setSamples(self):
#		sampleFiles  = [f for f in self.find_log_files(config.sp['metagenomics']['samples'])]
#		assert len(sampleFiles) == 1
#		sampleFile = sampleFiles[0]
#		samples = {}
#		conds = {}
#		with openMaybeZip(sampleFile['fn']) as sF:
#			for line in sF:
#				sampleName = line.strip()
#				condition = sampleName.split('-')[1]
#				samples[sampleName] = Sample(sampleName,condition)
#				if condition not in conds:
#					conds[condition] = []
#				conds[condition].append( samples[sampleName])
#		self.samples = samples
#		self.conditions = conds

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

	def buildPhylogenyTreeMaps(self):

		def oneTreemap(samples, rootnode, condition):

			def rMakeDict(node, getter,compGetter):
				if node.isleaf():
					val = getter(node)
					compval = compGetter(node)
					if val < 2 and compval < 2:
						return None
					name = node.name
					if name == 'NA':
						name = 'Unknown_{}'.format(self.taxa_hierarchy[-1])
					return node.name, val, compval
				out = {}
				comparator = {}
				for child in node:
					rout = rMakeDict(child,getter, compGetter)
					if rout == None:
						continue
					cname, val, compval = rout
					out[cname] = val
					comparator[cname] = compval
				out['size'] = getter(node)
				comparator['size'] = compGetter(node)
				if len(out) == 0:
					return None
				name = node.name
				if name == 'NA':
					rankI = node.height - self.root_offset
					if rankI < 0:
						name ='Unknown_High_Taxon'
					elif rankI > len(self.taxa_hierarchy) - 1 :
						name = 'Unknown_Low_Taxon'
					else:
						name = 'Unknown_{}'.format(self.taxa_hierarchy[rankI])	

				return name, out, comparator

			def getter(node):
				numerator = 0
				for sample in samples:
					numerator += node.normCountsBySamples[sample]
				denominator = len(samples)
				return numerator / denominator

			comparatorgetter = lambda n: sum(n.normCountsBySamples.values())/len(n.normCountsBySamples)
			root, treeAsDict, compTree = rMakeDict(rootnode, getter, comparatorgetter)
			# treeAsDict = treeAsDict['Bacteria']['Firmicutes']['Clostridia']['Clostridiales']['Clostridiaceae']
			# compTree = compTree['Bacteria']['Firmicutes']['Clostridia']['Clostridiales']['Clostridiaceae']
			pconfig = {
						'id':'phylogeny_treemap_{}'.format(condition),
						'title':'Phylogeny Tree {}'.format(condition),
						'subtitle':'Full'
						}
			return treemap.plot((treeAsDict,compTree),pconfig=pconfig)

		treemaps = []
		for condition, samples in self.conditions.items():
			treemaps.append(oneTreemap(samples, self.phylo_tree.root, condition))
			# plot = "<p>Phylogeny Treemaps</p>\n"
			# plot += treemaps[-1]
			# self.sections.append({
			# 	'name' : "{} Tree Map".format(condition),
			# 	'anchor' : 'tree_map_{}'.format(condition),
			# 	'content' : plot
			# 	})

		plot = "<p>Phylogeny Treemaps</p>\n"
		for tMap in treemaps:
			plot += "{}\n".format(tMap)

		self.sections.append({
			'name' : 'Tree Maps',
			'anchor' : 'tree_maps',
			'content' : plot
			})

	def buildAlignmentStatsChart(self):
		config = {
			'id' : 'metagenomic_align_stats_plot',
			'title' : 'Alignment Statistics',
			'ylab' : 'Num. Reads',
			'cpswitch_counts_label': 'Number of Reads'
		}
		categories = [taxa for taxa in self.taxa_hierarchy]
		categories.append('gene')
		categories.append('unassigned')

		def getAlignmentStats(fname):
			"""
			Return a tuple of the form (sample, taxa, total_reads, aligned_reads)
			"""
			fn = fname['fn']
			fn = fn.split('/')[-1]
			sampleName = fn.split('.')[0]
			if 'gene' in fn:
				taxa = 'gene'
			else:
				taxa = fn.split('.')[1]
			with openMaybeZip(fname['fn']) as f:
				f.readline()
				totalReads, alignedReads, _ = f.readline().split()
				return (sampleName, taxa, int(totalReads), int(alignedReads))


		alignStats = {}
		for alignStatF in self.alignment_stat_files:
			sampleName, taxa, totalReads, alignedReads = getAlignmentStats(alignStatF)
			sample = self.samples[sampleName]
			if sample not in alignStats:
				alignStats[sample] = (totalReads,{taxa:alignedReads})
			else:
				alignStats[sample][1][taxa] = alignedReads

		plotData = {}
		for sample, (totalReads, stats) in alignStats.items():
			for taxa in self.taxa_hierarchy:
				nodes = self.phylo_tree.taxa[taxa].values()
				topAligned = sum([node.topAlignedSeqCountBySample[sample] for node in nodes])

				if sample.name not in plotData:
					plotData[sample.name] = {}
				plotData[sample.name][taxa] = topAligned

			totalAligned = sum(plotData[sample.name].values())
			nUnaligned = totalReads - totalAligned
			plotData[sample.name]['unassigned'] = nUnaligned


		plot = plots.bargraph.plot(plotData, cats=categories, pconfig=config)
		plot = """
				<p>The number of reads which were mapped to various taxonomic ranks and genes</p>
				{}
				""".format( plot)
		self.sections.append({
			'name' : 'Alignment Statistics',
			'anchor' : 'alignment_stats',
			'content' : plot
			})

	def buildAlphaDiversityCharts(self):
		diversity = {taxa:{condition:{} for condition in self.conditions.keys()} for taxa in self.taxa_hierarchy}
		for dfile in self.diversity_files:
			for taxa in self.taxa_hierarchy:
				if taxa in dfile['fn']:
					with openMaybeZip(dfile['fn']) as df:
						df.readline()
						for line in df:
							sampleName, sInd = line.split()
							sampleName = sampleName[:sampleName.index('_count')]
							sampleName = '-'.join(sampleName.split('.')) # parts of the pieline switch . and -
							sample = self.samples[sampleName]
							diversity[taxa][sample.condition][sample.name] = float(sInd)  
		diversityPlots = []
		for taxa in diversity.keys():
			plotData = []
			for condition in diversity[taxa].keys():
				allSInds = diversity[taxa][condition].values()
				dist = [
						condition,
						min(allSInds),
						percentile(allSInds,0.25),
						percentile(allSInds,0.5),
						percentile(allSInds,0.75),
						max(allSInds)
					]
				plotData.append(dist)
			pconfig = {'ylab':'Shannon Index', 'xlab':'Condition', 'title':'{} Diversity'.format(taxa), 'groups':self.conditions.keys()}
			diversityPlots.append( boxplot.plot({taxa:plotData},pconfig=pconfig))

		plot = """
				<p>The alpha diversity (Shannon index) across conditions at various taxonomic levels</p>
				<div class="row">
				"""

		htmlRows = []
		rowSize = 3
		for i, dPlot in enumerate(diversityPlots):
			if i % rowSize == 0:
				htmlRows.append([""]*rowSize)
			htmlRows[i / rowSize][i % rowSize] = dPlot

		plot += split_over_columns(htmlRows,rowwise=True)

		self.sections.append({
			'name' : 'Alpha Diversity',
			'anchor' : 'alpha_diversity',
			'content' : plot
			})

	def buildBetaDiversityCharts(self):

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
		norm_table = self.norm_count_tables[self.taxa_hierarchy[-1]]
		cols, rows = norm_table.getTable()
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
		allIntraSample = []
		for condition, samples in self.conditions.items():
			jsds = []
			for s1, s2 in itertools.combinations(samples,2):	
				jsds.append( jDists[s1][s2])
				allIntraSample.append(jDists[s1][s2])
			dist = [
						"{}".format(condition),
						min(jsds),
						percentile(jsds,0.25),
						percentile(jsds,0.5),
						percentile(jsds,0.75),
						max(jsds)
					]
			plotData.append(dist)

		allInterSample = []
		for c1,c2 in itertools.combinations(self.conditions.keys(),2):
			samples1 = self.conditions[c1]
			samples2 = self.conditions[c2]
			jsds = []
			for s1, s2 in itertools.combinations(samples1+samples2,2):
				jsds.append( jDists[s1][s2])
				allInterSample.append(jDists[s1][s2])
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
		self.sections.append({
			'name' : 'Beta Diversity',
			'anchor' : 'beta_diversity',
			'content' : plot
			})

	def buildPCACharts(self):
		axes_interest = 4

		pts = [f for f in self.find_log_files( config.sp['metagenomics']['pca']['points'])]
		print('TODO: actually pick out species')
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

	def buildRichnessCharts(self):
		pass

	def buildSignifPlots(self):

		def oneVolcanoPlot(table,taxaLvl,minLfc=0.5,maxApv=0.1,rarefier=0.1):
			cols, rows = table.getTable(sqlCmd="SELECT taxa, logFC, adj_P_Val, group1, group2 FROM {table_name} ")


			lava = {'not significant (rarefied)':[]}
			for taxa, lfc, apv, g1, g2 in rows:
				group = "{} {}".format(g1,g2)
				if abs(lfc) > minLfc and apv < maxApv:
					if group not in lava:
						lava[group] = []
					lava[group].append({'name':taxa, 'x':lfc, 'y':-math.log(apv,2)})
				elif random() <  rarefier: # rarify insignificant points so page loads faster 
					lava['not significant (rarefied)'].append([lfc,-math.log(apv,2)])

			return scatter.plot(lava, pconfig={
												'ylab':'Negative log of adjusted p value', 
												'xlab':'average log fold change', 
												'title':'{} Volcano Plot'.format(taxaLvl),
												'legend':True
												})

		def oneMaPlot(table,taxaLvl,minLfc=0.5,maxApv=0.1,rarefier=0.1):
			cols, rows = table.getTable(sqlCmd="SELECT taxa, logFC, adj_P_Val, AveExpr, group1, group2 FROM {table_name} ")

			lava = {'not significant (rarefied)':[]}
			for  taxa, lfc, apv, aE, g1, g2 in rows:
				group = "{} {}".format(g1,g2)
				if abs(lfc) > minLfc and apv < maxApv:
					if group not in lava:
						lava[group] = []
					lava[group].append({'name':taxa, 'y':lfc, 'x':aE})
				elif random() <  rarefier: # rarify insignificant points so page loads faster 
					lava['not significant (rarefied)'].append([aE,lfc])

			return scatter.plot(lava, pconfig={
												'ylab':'Ave. Log Fold Change', 
												'xlab':'Ave. Expression', 
												'title':'{} MA Plot'.format(taxaLvl),
												'legend':True
												})


		sigPlots = []
		for taxa in self.taxa_hierarchy:
			if taxa == 'genus':
				minLfc=0.75
				maxApv=0.05
				rarefier=0.05
			elif taxa == 'species':
				minLfc=1
				maxApv=0.01
				rarefier=0.01
			else:
				minLfc=0.5
				maxApv=0.1
				rarefier=0.1

			volcano = oneVolcanoPlot(self.diff_count_tables[taxa],taxa,minLfc,maxApv,rarefier)
			ma =  oneMaPlot(self.diff_count_tables[taxa],taxa,minLfc,maxApv,rarefier)
			sigPlots.append( (volcano,ma))


		plot = """
				<p>Volcano and MA plots at various taxonomic levels</p>
				"""
		plot += split_over_columns(sigPlots,rowwise=True)

		self.sections.append({
			'name' : 'Significance Plots',
			'anchor' : 'sig_plots',
			'content' : plot
			})
				
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

class TreeNode(object):

	def __init__(self, name, parent):
		self.name = name
		self.parent = parent
		self.children = {}
		self.seqCountsBySamples = {}
		self.normCountsBySamples = {}
		self.height = 0
		self.rfindheight(self.parent)

	def rfindheight(self,parent):
		if parent != None:
			self.height += 1
			self.rfindheight(parent.parent) 

	def __iter__(self):
		return iter(self.children.values())

	def isleaf(self):
		if self.children == None or len(self.children) == 0:
			return True
		return False

	def addNameIfNotPresent(self, name):
		if name not in self.children:
			node = TreeNode(name, self)
			self.children[name] = node

		return self.children[name]

	def findSeqCountsThatDidNotAlignToChildren(self):
		if self.name == 'NA' or self.height < 2:
			self.topAlignedSeqCountBySample = {sample:0 for sample,qty in self.seqCountsBySamples.items()}
			return

		childcount = {sample:0 for sample in self.seqCountsBySamples.keys()}
		for child in self:
			for sample, qty in child.seqCountsBySamples.items():
				try:
					childcount[sample] += qty
				except KeyError:
					print(self.name)
					print(sample)
					print childcount
					print('---')
					print self.seqCountsBySamples
					assert False

		self.topAlignedSeqCountBySample = {sample:qty for sample,qty in self.seqCountsBySamples.items()}
		for sample, qty in childcount.items():
			self.topAlignedSeqCountBySample[sample] -= qty

		for qty in self.topAlignedSeqCountBySample.values():
			try:
				assert qty >= 0
			except AssertionError:
				print(self.name)
				print(sample)
				print(qty)
				print('--- ')
				for key,val in self.seqCountsBySamples.items():
					print("{} : {}".format(key,val))
				print('---')
				for key,val in childcount.items():
					print("{} : {}".format(key,val))
				print('---')
				for key,val in self.children.items():
					print("{} : {}".format(key,val))
				assert False


class Tree(object):

	def __init__(self, root, taxa_hierarchy):
		self.root =root
		self.all_nodes = {root.name:root}
		self.taxa_hierarchy = taxa_hierarchy
		self.size = 1
		for node in self:
			self.size += 1
			self.all_nodes[node.name] = node
		self.populateTaxa()


	def populateTaxa(self):
		rootOffset = 2 # height of the first interesting rank (phylum) from the root
		self.taxa = {rank:{} for rank in self.taxa_hierarchy}
		for node in self:
			rankI = node.height - rootOffset
			if rankI < 0:
				continue
			rank = self.taxa_hierarchy[rankI]
			self.taxa[rank][node.name] = node

	def __iter__(self):
		
		def rIter( node):
			if node.isleaf():
				yield node
			else:
				yield node
				for child in node:
					for subchild in rIter(child):
						yield subchild

		for node in rIter(self.root):
			yield node

	def __get__(self,name):
		return self.all_nodes[name]

	def __str__(self):
		mOut = ''
		for node in self:
			out = "\t"*node.height
			rnode = node
			while rnode != None:
				out += rnode.name + ";"
				rnode = rnode.parent
			mOut += out 
			mOut += "\n"
		return mOut
