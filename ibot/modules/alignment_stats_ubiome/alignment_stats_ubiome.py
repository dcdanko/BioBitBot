from biobitbot.modules.base_module import BaseIBotModule
from biobitbot import plots
from random import random
import math
from biobitbot.utils.utils import *



class IBotModule(BaseIBotModule):

	def __init__(self):
		super(IBotModule,self).__init__(
						name='Alignment Statistics', 
						anchor='alignment_stats_ubiome',
						info='Show the proportion of reads mapping to various taxonomic ranks')

		self.intro += """
						<p>
						The number of reads which were mapped to various taxonomic ranks and genes
						</p>
						"""

	def buildChartSet(self, taxa_hierarchy, phylo_tree, samples, alignment_stat_files):

		alignStats = {}
		for alignStatF in alignment_stat_files:
			sampleName, taxa, totalReads, alignedReads = getAlignmentStats(alignStatF)
			sample = samples[sampleName]
			if sample not in alignStats:
				alignStats[sample] = (totalReads,{taxa:alignedReads})
			else:
				alignStats[sample][1][taxa] = alignedReads

		plotData = {}
		for sample, (totalReads, stats) in alignStats.items():
			for taxa in taxa_hierarchy:
				nodes = phylo_tree.taxa[taxa].values()
				topAligned = sum([node.topAlignedSeqCountBySample[sample] for node in nodes])

				if sample.name not in plotData:
					plotData[sample.name] = {}
				plotData[sample.name][taxa] = topAligned

			totalAligned = sum(plotData[sample.name].values())
			nUnaligned = totalReads - totalAligned
			plotData[sample.name]['unassigned'] = nUnaligned

		pconfig = {
			'id' : 'ubiome_align_stats',
			'title' : 'Alignment Statistics',
			'ylab' : 'Num. Reads',
			'cpswitch_counts_label': 'Number of Reads'
		}
		categories = [taxa for taxa in taxa_hierarchy]
		categories.append('unassigned')

		plot = plots.bargraph.plot(plotData, cats=categories, pconfig=pconfig)
		self.intro += plot


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