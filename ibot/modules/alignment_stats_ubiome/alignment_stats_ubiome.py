


class IBotModule(BaseIBotModule):

	def __init__(self):
		super(BaseIBotModule,self).__init__(
						name='Alignment Statistics', 
						anchor='alignment_stats_ubiome',
						info='Show the proportion of reads mapping to various taxonomic ranks')

		self.intro += """
						<p>
						The number of reads which were mapped to various taxonomic ranks and genes
						</p>
						"""


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