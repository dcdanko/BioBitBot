from ibot.modules.base_module import BaseIBotModule
from random import random
import math
import ibot.plots.scatterplot as scatter




class IBotModule(BaseIBotModule):

	def __init__(self):
		super(IBotModule,self).__init__(
						name='Significance Charts', 
						anchor='significance',
						info='Make volcano and MA charts')

		self.intro += """
						<p>
						Volcano and MA charts. These charts show points which are prominent and merit further investigation.
						Click and drag to select an area to zoom in.
						</p>
						"""

	def strictness(self, strict):
		if strict == 0:
			minLfc=0.5
			maxApv=0.1
			rarefier=0.1
		elif strict == 1:
			minLfc=0.75
			maxApv=0.05
			rarefier=0.05
		elif strict == 2:
			minLfc=1
			maxApv=0.01
			rarefier=0.01
		else:
			minLfc=1
			maxApv=0.001
			rarefier=0.005
		return minLfc, maxApv, rarefier

	def buildChartSet(self, name, table, idcol='ids',groups=None,strict=1):

		minLfc, maxApv, rarefier = self.strictness(strict)
		if groups == None:

			v = volcanoMultiGroup(table,name,idcol,minLfc,maxApv,rarefier)
			m = maMultiGroup(table,name,idcol,minLfc,maxApv,rarefier)
		else:
			assert len(groups) == 2
			v = volcano(table,groups,idcol,minLfc,maxApv,rarefier)
			m = ma(table,groups,idcol,minLfc,maxApv,rarefier)

		plot = self.split_over_columns([[v,m]],rowwise=True)

		self.sections.append({
			'name' : name,
			'anchor' : 'sig_plots_{}'.format(name),
			'content' : plot
			})



def volcano(table,groups,idcol,minLfc,maxApv,rarefier):
	cols, rows = table.getTable(sqlCmd="SELECT {}, logFC, adj_P_Val FROM {{table_name}} ".format(idcol))
	xmin = False
	xmax = False
	ymin = False
	ymax = False
	lava = {'not significant (rarefied)':[], 'significant':[]}
	for gene, lfc, apv in rows:
		yval = -math.log(apv,2)
		if abs(lfc) > minLfc and apv < maxApv:
			lava['significant'].append({'name':gene, 'x':lfc, 'y':yval})
		elif random() <  rarefier: # rarify insignificant points so page loads faster 
			lava['not significant (rarefied)'].append([lfc,yval])
		if not xmax or lfc > xmax:
			xmax = lfc
		elif not xmin or lfc < xmin:
			xmin = lfc
		if not ymax or yval > ymax:
			ymax = yval
		elif not ymin or yval < ymin:
			ymin = yval

	return scatter.plot(lava, pconfig={
										'ylab':'Negative log of adjusted p value', 
										'xlab':'average log fold change', 
										'title':'Volcano Plot {} v. {}'.format(*groups),
										'legend':True,
										'xmax':xmax,
										'xmin':xmin,
										'ymax':ymax,
										'ymin':ymin,
										})

def ma(table,groups,idcol,minLfc,maxApv,rarefier):
	cols, rows = table.getTable(sqlCmd="SELECT {}, logFC, adj_P_Val, AveExpr FROM {{table_name}} ".format(idcol))
	xmin = False
	xmax = False
	ymin = False
	ymax = False
	lava = {'not significant (rarefied)':[], 'significant':[]}
	for  gene, lfc, apv, aE in rows:
		if abs(lfc) > minLfc and apv < maxApv:
			lava['significant'].append({'name':gene, 'y':lfc, 'x':aE})
		elif random() <  rarefier: # rarify insignificant points so page loads faster 
			lava['not significant (rarefied)'].append([aE,lfc])
		if not xmax or aE > xmax:
			xmax = aE
		elif not xmin or aE < xmin:
			xmin = aE
		if not ymax or lfc > ymax:
			ymax = lfc
		elif not ymin or lfc < ymin:
			ymin = lfc

	return scatter.plot(lava, pconfig={
										'ylab':'Ave. Log Fold Change', 
										'xlab':'Ave. Expression', 
										'title':'MA Plot {} v. {}'.format(*groups),
										'legend':True,
										'xmax':xmax,
										'xmin':xmin,
										'ymax':ymax,
										'ymin':ymin,

										})

def volcanoMultiGroup(table,name,idcol,minLfc,maxApv,rarefier):
	cols, rows = table.getTable(sqlCmd="SELECT {}, logFC, adj_P_Val, group1, group2 FROM {{table_name}} ".format(idcol))
	xmin = False
	xmax = False
	ymin = False
	ymax = False

	lava = {'not significant (rarefied)':[]}
	for taxa, lfc, apv, g1, g2 in rows:
		group = "{} {}".format(g1,g2)
		yval = -math.log(apv,2)
		if abs(lfc) > minLfc and apv < maxApv:
			if group not in lava:
				lava[group] = []
			lava[group].append({'name':taxa, 'x':lfc, 'y':yval})
		elif random() <  rarefier: # rarify insignificant points so page loads faster 
			lava['not significant (rarefied)'].append([lfc,yval])
		if not xmax or lfc > xmax:
			xmax = lfc
		elif not xmin or lfc < xmin:
			xmin = lfc
		if not ymax or yval > ymax:
			ymax = yval
		elif not ymin or yval < ymin:
			ymin = yval

	return scatter.plot(lava, pconfig={
										'ylab':'Negative log of adjusted p value', 
										'xlab':'average log fold change', 
										'title':'{} Volcano Plot'.format(name),
										'legend':True,
										'xmax':xmax,
										'xmin':xmin,
										'ymax':ymax,
										'ymin':ymin,
										})

def maMultiGroup(table,taxaLvl,idcol,minLfc,maxApv,rarefier):
	cols, rows = table.getTable(sqlCmd="SELECT {}, logFC, adj_P_Val, AveExpr, group1, group2 FROM {{table_name}} ".format(idcol))
	xmin = False
	xmax = False
	ymin = False
	ymax = False
	lava = {'not significant (rarefied)':[]}
	for  taxa, lfc, apv, aE, g1, g2 in rows:
		group = "{} {}".format(g1,g2)
		if abs(lfc) > minLfc and apv < maxApv:
			if group not in lava:
				lava[group] = []
			lava[group].append({'name':taxa, 'y':lfc, 'x':aE})
		elif random() <  rarefier: # rarify insignificant points so page loads faster 
			lava['not significant (rarefied)'].append([aE,lfc])
		if not xmax or aE > xmax:
			xmax = aE
		elif not xmin or aE < xmin:
			xmin = aE
		if not ymax or lfc > ymax:
			ymax = lfc
		elif not ymin or lfc < ymin:
			ymin = lfc

	return scatter.plot(lava, pconfig={
										'ylab':'Ave. Log Fold Change', 
										'xlab':'Ave. Expression', 
										'title':'{} MA Plot'.format(taxaLvl),
										'legend':True,
										'xmax':xmax,
										'xmin':xmin,
										'ymax':ymax,
										'ymin':ymin,
										})