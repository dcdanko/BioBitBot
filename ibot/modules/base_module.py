#!/usr/bin/env python

""" 
iBot module base class.

Modules provide the raw html necessary to create a report.

Modules can provide html either appended to the self.intro variable
or as a dictionary in the self.sections list.

Modules take in parsed data (from their parent analysis) do light
data analysis and make calls to plotting functions.

The bulk of html production is done by plotting functions but modules 
can add some html themselves.
"""


import fnmatch
import glob
import io
import logging
import os
import random

from multiqc.utils import report, config
logger = logging.getLogger(__name__)

letters = 'abcdefghijklmnopqrstuvwxyz'

class BaseIBotModule(object):

    def __init__(self, name='base', anchor='base', target='',href='', info='', extra=''):
        self.name = name
        self.anchor = anchor
        if not target:
            target = self.name
        self.intro = '<p><a href="{0}" target="_blank">{1}</a> {2}</p>{3}'.format(
            href, target, info, extra
        )
        self.sections = []

    def split_over_columns(self, els, rowwise=False):
        """
        Given a list of lists of strings containing html 
        split the strings into multiple html 'columns' using
        bootstraps framework.
        @parameter List of lists of strings. Each sub list is a column. Up to 12 columns.

        @return Valid html string.
        """
        if not rowwise:
            ncols = len(els)
            assert ncols <= 12
            rows = []
            for sublist in els:
                for i, el in enumerate(sublist):
                    if len(rows) <= i:
                        rows.append([])
                    rows[i].append(el)
        else:
            rows = els
            rowsizes = [len(row) for row in rows]
            ncols = max(rowsizes)
            assert ncols <= 12

        colsize = 12 / ncols

        outstr = """
                 """
        for i, row in enumerate(rows):
            outstr += """
                        <div class="row">
                      """
            for j, el in enumerate(row):
                outstr += """
                            <div class="col-md-{}">
                                {}
                            </div>
                          """.format(colsize,el)
            outstr += """
                        </div>
                      """
        return outstr

