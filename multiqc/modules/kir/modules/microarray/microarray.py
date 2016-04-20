#!/usr/bin/env python

""" MultiQC module to parse output from CGAT Microarray Differential Expression Pipeline"""


from collections import OrderedDict
import logging
import re

from multiqc import config, BaseMultiqcModule
from multiqc.plots.data_table import DataTable

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):

    def __init__(self):

        # Initialise the parent object
        super(MultiqcModule, self).__init__(name='Microarray Analysis', anchor='microarray', 
        href="https://en.wikipedia.org/wiki/Comma-separated_values", 
        info="Displays a CSV (or similar) file.")

        self.data_tables = [] 
        # Find and load any differential expression reports
        self.data = dict()
        print([f for f in self.find_log_files(config.sp['microarray']['diff_exp'])])
        for f in self.find_log_files(config.sp['csv_table']):
            filename = f['root'] + '/' + f['fn']
            dt = DataTable.parseCSVFileToTable(filename,filename,header=True)
            self.data_tables.append(dt)


        if len(self.data_tables) == 0:
            log.debug("Could not find any reports in {}".format(config.analysis_dir))
            raise UserWarning
        log.info("Found {} reports".format(len(self.data_tables)))

        for table in self.data_tables:
            self.intro += table.as_html()