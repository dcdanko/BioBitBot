
class IBotModule(BaseIBotModule):

	def __init__(self):
		super(BaseIBotModule,self).__init__(
						name='Alpha Diversity', 
						anchor='alpha_diversity',
						info='The intrasample diversity across conditions')

		self.intro += """
						<p>
						The intrasample diversity across conditions.
						</p>
						"""



	def buildChartSet(self, conditions, samples, diversity_files, taxa_hierarchy):
		diversity = {taxa:{condition:{} for condition in conditions.keys()} for taxa in taxa_hierarchy}
		for dfile in diversity_files:
			for taxa in taxa_hierarchy:
				if taxa in dfile['fn']:
					with openMaybeZip(dfile['fn']) as df:
						df.readline()
						for line in df:
							sampleName, sInd = line.split()
							sampleName = sampleName[:sampleName.index('_count')]
							sampleName = '-'.join(sampleName.split('.')) # parts of the pieline switch . and -
							sample = samples[sampleName]
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
			pconfig = {'ylab':'Shannon Index', 'xlab':'Condition', 'title':'{} Diversity'.format(taxa), 'groups':conditions.keys()}
			diversityPlots.append( boxplot.plot({taxa:plotData},pconfig=pconfig))

		htmlRows = []
		rowSize = 3
		for i, dPlot in enumerate(diversityPlots):
			if i % rowSize == 0:
				htmlRows.append([""]*rowSize)
			htmlRows[i / rowSize][i % rowSize] = dPlot

		plot = split_over_columns(htmlRows,rowwise=True)
		self.intro += plot