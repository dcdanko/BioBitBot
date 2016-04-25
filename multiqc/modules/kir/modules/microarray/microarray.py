#!/usr/bin/env python

""" MultiQC module to parse output from CGAT Microarray Differential Expression Pipeline"""


from collections import OrderedDict
import logging
import re
import csv
from multiqc import config, BaseMultiqcModule
from multiqc.plots.sql_data_table import SqlDataTable
import multiqc.plots.scatterplot as scatter
import multiqc.plots.boxplot as boxplot
import math
from random import random

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
        rawFiles = [rF for rF in self.find_log_files(config.sp['microarray']['raw_data'])]
        assert len(rawFiles) == 1
        self.rawData = self.parseRawDataTable(rawFiles[0]['fn'])
        self.diffExp = self.parseDiffExpTable(diffFiles[0]['fn'])
        self.buildProbeGeneMaps()

        self.intro += self.volcanoPlot()
        self.intro += self.maPlot()
        self.intro += self.geneBoxPlot('FAM20C', isgene=True)
        self.intro += self.diffExp.as_html(sqlCmd="SELECT  * FROM {table_name} WHERE adj_P_Val < 0.005 AND AveExpr > 8")

    def buildProbeGeneMaps(self):

        cols, rows = self.diffExp.getTable(sqlCmd= "SELECT Probe, gene FROM {table_name}")
        self.probeToGenes = {}
        self.genesToProbes = {}
        for probe, gene in rows:
            self.probeToGenes[probe] = gene
            if gene not in self.genesToProbes:
                self.genesToProbes[gene] = [probe]
            else:
                self.genesToProbes[gene].append(probe)

    def geneBoxPlot(self, probe, isgene=False):
        pconfig = {'ylab':'Expression Level', 'xlab':'Condition', 'title':'{} Expression Levels'.format(probe)}
        if not isgene:
            cols, rows = self.rawData.getTable(sqlCmd="SELECT * FROM {table_name} WHERE Probe == " + probe)
        else:
            probes = self.genesToProbes[probe]
            sqlList = '(' + ', '.join(probes) + ')'
            cols, rows = self.rawData.getTable(sqlCmd="SELECT * FROM {table_name} WHERE Probe IN " + sqlList)
        # assert len(rows) == 1
        groups = {}
        for row in rows:
            if isgene:
                for col, el in zip(cols,row):
                    group = col.name.strip().strip('"').split('_')[0]
                    if group == 'Probe':
                        curProbe = el
            for col, el in zip(cols,row):
                group = col.name.strip().strip('"').split('_')[0]
                if group != 'Probe':
                    if isgene:
                        group += '_' + curProbe
                    if group in groups:
                        groups[group].append(el)
                    else:
                        groups[group] = [el]

        series = {}
        for group, data in groups.items():
            data = sorted(data)
            dist = [
                        group,
                        min(data),
                        percentile(data,0.25),
                        percentile(data,0.5),
                        percentile(data,0.75),
                        max(data)
                    ]
            series[group] = dist
        if isgene:
            pconfig['groups'] = sorted(sorted(groups.keys()), key = lambda x: x.split('_')[1])
        else:
            pconfig['groups'] = sorted(groups.keys())

        print(pconfig['groups'])

        sseries = []
        for group in pconfig['groups']:
            sseries.append( series[group])

        pdata = {probe:sseries}
        # if not isgene:
        #     pdata = {probe:series}
        # else:
        #     pdata = {}
        #     for dist in series:
        #         p = dist[0].split('_')[1]
        #         if p not in pdata:
        #             pdata[p] = [dist]
        #         else:
        #             pdata[p].append(dist)

        # print(pdata)
        return boxplot.plot(pdata,pconfig=pconfig)



    def volcanoPlot(self):
        cols, rows = self.diffExp.getTable(sqlCmd="SELECT gene, logFC, adj_P_Val FROM {table_name} ")

        lava = {'not significant (rarefied)':[], 'significant':[]}
        for gene, lfc, apv in rows:
            if abs(lfc) > 0.5 and apv < 0.1:
                lava['significant'].append({'name':gene, 'x':lfc, 'y':-math.log(apv,2)})
            elif random() <  0.1: # rarify insignificant points so page loads faster 
                lava['not significant (rarefied)'].append([lfc,-math.log(apv,2)])

        return scatter.plot(lava, pconfig={'ylab':'Negative log of adjusted p value', 'xlab':'average log fold change', 'title':'Volcano Plot'})

    def maPlot(self):
        cols, rows = self.diffExp.getTable(sqlCmd="SELECT gene, logFC, adj_P_Val, AveExpr FROM {table_name} ")

        lava = {'not significant (rarefied)':[], 'significant':[]}
        for gene, lfc, apv, aE in rows:
            if abs(lfc) > 0.5 and apv < 0.1:
                lava['significant'].append({'name':gene, 'y':lfc, 'x':aE})
            elif random() <  0.1: # rarify insignificant points so page loads faster 
                lava['not significant (rarefied)'].append([aE,lfc])

        return scatter.plot(lava, pconfig={
                                    'ylab':'Ave. Log Fold Change', 
                                    'xlab':'Ave. Expression', 
                                    'title':'MA Plot'})

    def parseRawDataTable(self, filename):
        dt = SqlDataTable('raw_data')
        with open(filename) as rD:
            header = rD.readline()
            for col in header.split('\t'):
                col = '_'.join(col.strip().split('.'))
                if 'ids' in col:
                    dt.addColumnInfo('Probe', 'TEXT')
                else:
                    dt.addColumnInfo(col, 'FLOAT')
            dt.initSqlTable()
            rdr = csv.reader(rD,delimiter='\t')
            dt.addManyRows(rdr)
        return dt


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
            rdr = csv.reader(dE,delimiter='\t')
            dt.addManyRows(rdr)
        return dt




def percentile(N, percent, key=lambda x:x):
    """
    Find the percentile of a list of values.

    @parameter N - is a list of values. Note N MUST BE already sorted.
    @parameter percent - a float value from 0.0 to 1.0.
    @parameter key - optional key function to compute value from each element of N.

    @return - the percentile of the values
    """
    if not N:
        return None
    k = (len(N)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0+d1