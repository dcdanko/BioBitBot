from ibot.modules.base_module import BaseIBotModule
from collections import OrderedDict
import itertools
import ibot.plots.scatterplot as scatter

class IBotModule(BaseIBotModule):

	def __init__(self):
		super(IBotModule,self).__init__(
						name='Principle Component Analysis', 
						anchor='pca',
						info='PCA plots of sample data')

		self.intro += """
						<p>
						Charts of major principal components. 
						These components show possible clusterings.
						Click and drag to select an area to zoom in.
						</p>
						"""

	def buildChartSet(self, ptsFilename, veFilename, conditions, axes_interest=4):
		points = {}
		with open(ptsFilename) as pF:
			pF.readline()
			for line in pF:
				line = line.split()
				# print(line)
				condition = getConditionsFromName('-'.join(line[0].strip().split('.')),conditions)[0]
				vals = [float(pt) for pt in line[1:]]
				if condition not in points:
					points[condition] = []
				points[condition].append(vals[:axes_interest])

		with open(veFilename) as vF:
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
			for condition in conditions:
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

		self.intro += """
				<p>The first {} principal components which explain {:.1f}% of the variation in the data.</p>
				""".format(axes_interest, 100*sum(axes))
		htmlRows = []
		rowSize = 3
		for i, aPlot in enumerate(plots):
			if i % rowSize == 0:
				htmlRows.append([""]*rowSize)
			htmlRows[i / rowSize][i % rowSize] = aPlot

		self.intro += self.split_over_columns(htmlRows,rowwise=True)

		

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
