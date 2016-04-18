#!/usr/bin/env python

""" MultiQC module to parse output from CGAT Microarray Differential Expression Pipeline"""


from collections import OrderedDict
import logging
import re

from multiqc import config, BaseMultiqcModule

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):

	def __init__(self):

        # Initialise the parent object
        super(MultiqcModule, self).__init__(name='DiffExp', anchor='diff_exp', 
        href="https://github.com/CGATOxford/CGATPipelines/tree/master/CGATPipelines", 
        info=" analyzes differentially expressed genes from a microarray or RNASeq experiment.")

        # Find and load any STAR reports
        self.diffexp_data = dict()
        for f in self.find_log_files(config.sp['diff_exp']):
            parsed_data = self.parse_diff_exp(f['f'])
            if parsed_data is not None:
                s_name = f['s_name'].split('Log.final.out', 1)[0]
                if s_name in self.star_data:
                    log.debug("Duplicate sample name found! Overwriting: {}".format(s_name))
                self.add_data_source(f, s_name)
                self.star_data[s_name] = parsed_data

        if len(self.star_data) == 0:
            log.debug("Could not find any reports in {}".format(config.analysis_dir))
            raise UserWarning

        log.info("Found {} reports".format(len(self.star_data)))

        # Write parsed report data to a file
        self.write_data_file(self.star_data, 'multiqc_star')

        # Basic Stats Table
        self.star_stats_table()

        # Alignment bar plot - only one section, so add to the module intro
        self.intro += self.star_alignment_chart()