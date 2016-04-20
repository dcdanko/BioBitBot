#!/usr/bin/env python

""" MultiQC module to parse output from CGAT Microarray Differential Expression Pipeline"""


from collections import OrderedDict
import logging
import re
import csv
from multiqc import config, BaseMultiqcModule
from multiqc.plots.data_table import DataTable
from multiqc.plots.sql_data_table import SqlDataTable

# Initialise the logger
log = logging.getLogger(__name__)


class MultiqcModule(BaseMultiqcModule):

    def __init__(self):

        # Initialise the parent object
        super(MultiqcModule, self).__init__(name='Microarray Analysis', anchor='microarray', 
        href="https://en.wikipedia.org/wiki/Comma-separated_values", 
        info="Displays the results of differential expression analysis on a microarray")

        self.data_tables = [] 
        # Find and load any differential expression reports
        diffFiles = [dF for dF in self.find_log_files(config.sp['microarray']['diff_exp'])]
        assert len(diffFiles) == 1
        self.diffExp = self.parseDiffExpTable(diffFiles[0]['fn'])
        self.intro += self.diffExp.as_html()

    def parseDiffExpTable(self,filename):
        dt = SqlDataTable('diff_exp')
        dt.addColumnInfo('Probe','TEXT')
        dt.addColumnInfo('logFC','FLOAT')
        dt.addColumnInfo('AveExpr','FLOAT')
        dt.addColumnInfo('t','FLOAT')
        dt.addColumnInfo('P_Value','FLOAT')
        dt.addColumnInfo('adj_P_Val','FLOAT')
        dt.addColumnInfo('B','FLOAT')
        dt.addColumnInfo('gene','TEXT')
        dt.initSqlTable()
        with open(filename) as dE:
            dE.readline()
            rdr = csv.reader(dE)
            dt.addManyRows(rdr)
        return dt




