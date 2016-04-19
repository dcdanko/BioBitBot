#!/usr/bin/env python

""" MultiQC module to parse output from CGAT Microarray Differential Expression Pipeline"""


from collections import OrderedDict
import logging
import re

from multiqc import config, BaseMultiqcModule
from multiqc.utils.data_table import DataTable

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):

	def __init__(self):

		# Initialise the parent object
		super(MultiqcModule, self).__init__(name='DiffExp', anchor='diff_exp', 
		href="https://github.com/CGATOxford/CGATPipelines/tree/master/CGATPipelines", 
		info=" analyzes differentially expressed genes from a microarray or RNASeq experiment.")

		# Find and load any differential expression reports
		self.diff_exp_data = dict()
		for f in self.find_log_files(config.sp['diff_exp']):
			filename = f['root'] + f['s_name']
			print(filename)
			self.intro += self.diff_exp_data_table(filename)
			# parsed_data = self.parse_diff_exp(f['f'])
			# if parsed_data is not None:
			#     s_name = f['s_name'].split('Log.final.out', 1)[0]
			#     if s_name in self.diff_exp_data:
			#         log.debug("Duplicate sample name found! Overwriting: {}".format(s_name))
			#     self.add_data_source(f, s_name)
			#     self.diff_exp_data[s_name] = parsed_data

		if len(self.diff_exp_data) == 0:
			log.debug("Could not find any reports in {}".format(config.analysis_dir))
			raise UserWarning

		log.info("Found {} reports".format(len(self.star_data)))




		

	def diff_exp_data_table(self,filename):
		dt = DataTable(filename)
		dt.parseCSVFile(filename,sep='\t',header=True)
		return dt.as_html()



