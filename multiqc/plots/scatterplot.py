#!/usr/bin/env python

""" MultiQC functions to plot a report scatterplot """

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

from multiqc.utils import report, config
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
		""".format(id=pconfig['id'], d=json.dumps(plotdata), c=json.dumps(pconfig));
	
	# jsHead = """
	# 		$(function () {{
	# 		$('{id}').highcharts({{
	# 			chart: {{
	# 				type: 'scatter',
	# 				zoomType: 'xy'
	# 			}},
	# 			title: {{
	# 				text: '{title}'
	# 			}},
	# 			xAxis: {{
	# 				title: {{
	# 					enabled: true,
	# 					text: '{x_label}'
	# 				}},
	# 				startOnTick: true,
	# 				endOnTick: true,
	# 				showLastLabel: true
	# 			}},
	# 			yAxis: {{
	# 				title: {{
	# 					text: '{y_label}'
	# 				}}
	# 			}},
	# 			legend: {{
	# 				layout: 'vertical',
	# 				align: 'left',
	# 				verticalAlign: 'top',
	# 				x: 100,
	# 				y: 70,
	# 				floating: true,
	# 				backgroundColor: (Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF',
	# 				borderWidth: 1
	# 			}},
	# 			plotOptions: {{
	# 				scatter: {{
	# 					marker: {{
	# 						radius: 5,
	# 						states: {{
	# 							hover: {{
	# 								enabled: true,
	# 								lineColor: 'rgb(100,100,100)'
	# 							}}
	# 						}}
	# 					}},
	# 					states: {{
	# 						hover: {{
	# 							marker: {{
	# 								enabled: false
	# 							}}
	# 						}}
	# 					}},
	# 					tooltip: {{
	# 						headerFormat: '<b>{{series.name}}</b><br>',
	# 						pointFormat: '{{point.x}} cm, {{point.y}} kg'
	# 					}}
	# 				}}
	# 			}},
	# 			""".format(id=pconfig['id'],title='fee',x_label='fie', y_label='fau')

	# jsSeriesTemplate = """
	# 			series: [{{
	# 				name: '{population_name}',
	# 				color: '{population_color}',
	# 				data : {population_data}
	# 			}}]
	# 			"""

	# js += jsHead
	# for popName, population in plotdata.items():
	# 	js += jsSeriesTemplate.format(population_name=popName,population_color=None,population_data=population)
	# js += "</script>\n"

	report.num_hc_plots += 1
	html += js
	return html