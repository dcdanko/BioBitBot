
class IBotFileError(Exception):
	pass

class IBotMetadataError(IBotFileError):
	def __init__(self,n):
		self.n = n

	def __str__(self):
		if self.n == 0:
			return('No metadata file found')
		else:
			return('{} metadata files found.'.format(self.n))
