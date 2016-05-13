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