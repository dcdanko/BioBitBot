from ibot.modules.base_module import BaseIBotModule
import itertools
import math
import ibot.plots.boxplot as boxplot

class IBotModule(BaseIBotModule):

	def __init__(self):
		super(IBotModule,self).__init__(
						name='Distance charts', 
						anchor='distance',
						info='intersample distances between and within conditions')

		self.intro += """
						<p>
						Intersample distances. These charts show the distances between samples between and with conditions.
						This is largely analagous to Beta-Diversity for ecological applications.
						</p>
						"""

	def buildChartSet(self,table,conditions,idcol='ids'):
		metrics = [
					(JSD,'jensen-shannon distance'),
					(COS,'cosine similarity'),
					]
		for metric, metricName in metrics:
			chart = oneChart(metricName,table,conditions,metric,idcol)
			self.sections.append({
				'name' : metricName.title(),
				'anchor' : 'distance_{}'.format(metricName),
				'content' : chart
				})

def oneChart(metricName, table,conditions,metric,idcol):
	cols, rows = table.getTable()
	samples = [col.name for col in cols if idcol not in col.name]
	norm_sample = {sample:[] for sample in samples}
	for row in rows:
		for i,col in enumerate(cols):
			if col.name == idcol:
				continue
			norm_sample[col.name].append(row[i])

	distTable = { sample : {sample:1 for sample in samples} for sample in samples}
	for s1, s2 in itertools.combinations(samples,2):
		distance = metric(norm_sample[s1], norm_sample[s2])
		distTable[s1][s2] = distance
		distTable[s2][s1] = distance

	plotData = []
	for condition in conditions:
		matchingSamples = []
		for sample in samples:
			if condition in getConditionsFromName(sample,conditions):
				matchingSamples.append(sample)
		distances = []
		for s1, s2 in itertools.combinations(matchingSamples,2):	
			distances.append( distTable[s1][s2])
		distribution = [
					"{}".format(condition),
					min(distances),
					percentile(distances,0.25),
					percentile(distances,0.5),
					percentile(distances,0.75),
					max(distances)
				]
		plotData.append(distribution)

	for c1,c2 in itertools.combinations(conditions,2):
		matchingSamples1 = []
		for sample in samples:
			if c1 in getConditionsFromName(sample,conditions):
				matchingSamples1.append(sample)
		matchingSamples2 = []
		for sample in samples:
			if c2 in getConditionsFromName(sample,conditions):
				matchingSamples2.append(sample)
		distances = []
		for s1 in matchingSamples1:
			for s2 in matchingSamples2:
				distances.append( distTable[s1][s2])
		distribution = [
					"{} {}".format(c1,c2),
					min(distances),
					percentile(distances,0.25),
					percentile(distances,0.5),
					percentile(distances,0.75),
					max(distances)
				]
		plotData.append(distribution)

	pconfig = {
				'ylab':metricName, 
				'xlab':'Condition', 
				'title':metricName.title(), 
				'groups':conditions
				}
	bPlot = boxplot.plot({'distances':plotData},pconfig=pconfig)
	plot = "<p>The {} across and between conditions</p>\n".format(metricName.title())
	plot += bPlot
	return plot

def COS(A,B):
	assert len(A) == len(B)
	magA = math.sqrt( sum([el*el for el in A]))
	magB = math.sqrt( sum([el*el for el in B]))
	dot = 0.0
	for a,b in zip(A,B):
		dot += a*b

	return dot/(magA*magB)	

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