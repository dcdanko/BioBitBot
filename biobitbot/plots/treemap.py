#!/usr/bin/env python

""" BioBitBot functions to plot a report scatterplot """

import base64
import io
import json
import logging
import os
import random

# Import matplot lib but avoid default X environment
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from biobitbot.utils import report, config
logger = logging.getLogger(__name__)

letters = 'abcdefghijklmnopqrstuvwxyz'

# Load the template so that we can access it's configuration
template_mod = config.avail_templates[config.template].load()

def plot (data, pconfig={}):
	"""
	expects data to be a list with two nested series of dictionaries with labels as keys
	First dictionary is the actual data
	Second dictionary is a comparator to produce color
	"""
	assert len(data) == 2
	assert type(data[0]) == dict 
	assert type(data[1]) == dict 
	return highcharts_treemap(data, pconfig=pconfig)
	   

def highcharts_treemap(plotdata, pconfig={}):
	
	# Build the HTML for the page
	if pconfig.get('id') is None:
		pconfig['id'] = 'mqc_hcplot_'+''.join(random.sample(letters, 10))
	html = '<div class="mqc_hcplot_plotgroup">'

	
	# The plot div
	html += '<div class="hc-plot-wrapper"><div id="{id}" class="hc-plot not_rendered"><small>loading..</small></div></div></div> \n'.format(id=pconfig['id'])

	# Javascript with data dump
	js = """
		<script type="text/javascript">
		mqc_plots["{id}"] = {{
			"plot_type": "treemap",
			"datasets": {d},
			"config": {c}
		}}
		</script>
		""".format(id=pconfig['id'], d=json.dumps(plotdata), c=json.dumps(pconfig));
	

	report.num_hc_plots += 1
	html += js
	return html