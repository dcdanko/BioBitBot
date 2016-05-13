#!/usr/bin/env python

""" iBot functions to plot a report scatterplot """

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

from ibot.utils import report, config
logger = logging.getLogger(__name__)

letters = 'abcdefghijklmnopqrstuvwxyz'

# Load the template so that we can access it's configuration
template_mod = config.avail_templates[config.template].load()

def plot (data, pconfig={}):
	""" Plot a scatter graph with X,Y data. See CONTRIBUTING.md for
	further instructions on use.
	:param data: Dictionary of lists of 2-ples. Each list is a seperate population with name as its key.
	:param pconfig: optional dict with config key:value pairs. See CONTRIBUTING.md
	:return: HTML and JS, ready to be inserted into the page
	"""
	plotdata = []
	for key, series in data.items():
		plotdata.append({'name':key,'data':series})

	return highcharts_scatterplot(plotdata, pconfig)
	   




def highcharts_scatterplot(plotdata, pconfig={}):
	
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
			"plot_type": "xy_scatter",
			"datasets": {d},
			"config": {c}
		}}
		</script>
		""".format(id=pconfig['id'], d=json.dumps(plotdata), c=json.dumps(pconfig))

	report.num_hc_plots += 1
	html += js
	return html