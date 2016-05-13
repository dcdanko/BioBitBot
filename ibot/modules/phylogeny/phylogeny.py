import ibot.plots.treemap as treemap
from ibot.modules.base_module import BaseIBotModule
from random import random
import math
from ibot.utils.utils import *

class IBotModule(BaseIBotModule):

	def __init__(self):
		super(IBotModule,self).__init__(
						name='Phylogeny TreeMap', 
						anchor='phylogeny',
						info='TreeMap of a phylogeny tree')

		self.intro += """
						<p>
						TreeMap of phylogeny. The size of a box shows is proportional to
						its relative abundance. The color of a box indicates if a group
						is enriched or rarefied compared to the average.
						</p>
						"""

	def buildChartSet(self, conditions, phylo_tree,taxa_hierarchy,root_offset):
		for condition, samples in conditions.items():
			tMap = self.oneTreemap(samples, phylo_tree.root, condition,taxa_hierarchy,root_offset)
			self.sections.append({
				'name' : '{} Tree Map'.format(condition.title()),
				'anchor' : '{}_tree_map'.format(condition),
				'content' : tMap
				})


	def oneTreemap(self, samples, rootnode, condition,taxa_hierarchy,root_offset):

		def rMakeDict(node, getter,compGetter):
			if node.isleaf():
				val = getter(node)
				compval = compGetter(node)
				if val < 2 and compval < 2:
					return None
				name = node.name
				if name == 'NA':
					name = 'Unknown_{}'.format(taxa_hierarchy[-1])
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
				rankI = node.height - root_offset
				if rankI < 0:
					name ='Unknown_High_Taxon'
				elif rankI > len(taxa_hierarchy) - 1 :
					name = 'Unknown_Low_Taxon'
				else:
					name = 'Unknown_{}'.format(taxa_hierarchy[rankI])	

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