#!/usr/bin/env python

from collections import OrderedDict


class DataTableColumnInfo(object):
	
	def __init__(self, table, name):
		self.table = table
		self.name = name # Same as 'title' in other parts of the general_stats table
		self.description = ''
		self.cmax = float('inf')
		self.cmin = float('-inf')
		self.scale = 'GnBu'
		self.format = '{:.1f}'


class DataTableRow(object):
	
	def __init__(self, table, rowName, rowData, missingVal=None):
		self.table = table
		self.name = rowName
		self.data = rowData
		self.missingVal = missingVal
		self.fillMissingColumnsWithDefault()


	def fillMissingColumnsWithDefault(self):
		for columnInfo in self.table.columns():
			colName = columnInfo.name
			if colName not in self.data:
				self.data[colName] = missingVal

	def changeElement(self,colname,newVal):
		if colname in self.table.columns.keys():
			self.data[colname] = newVal
		else:
			assert False # TODO real exception


class DataTable(object):

	def __init__(self):
		self.columns = OrderedDict()
		self.rows = OrderedDict()

	# Inelegant but probably easy to use
	def addColumnInfo(self, name, 
						descrip=None, 
						cmax=None, 
						cmin=None, 
						scale=None, 
						format=None):
		newColumnInfo = DataTableColumnInfo(self,name)
		if description:
			newColumnInfo.description = descrip
		if cmax:
			newColumnInfo.cmax = cmax
		if cmin:
			newColumnInfo.cmin = cmin
		if scale:
			newColumnInfo.scale = scale
		if format:
			newColumnInfo.format = format

		self.columns[name] = newColumnInfo
		for row in self.rows.values():
			row.fillMissingColumns()

	def addRow(self, rowName, data, missingVal=None):
		newRow = DataTableRow(rowName,data,missingVal=missingVal)

	def as_html(self):
		table_html = {
						'columns': OrderedDict(),
						'rows': defaultdict(lambda:dict())
					}

		for colName, column in self.columns.items():
			table_html['columns'][colName] = '<th \
						id="header_{colName}" \
						class="chroma-col {colName}" \
						data-chroma-scale="{scale}" \
						data-chroma-max="{max}" \
						data-chroma-min="{min}" \
						{sk}><span data-toggle="tooltip" \
						title="{descrip}" \
						>{title}</span></th>'.format(
													colName=colName, 
													scale=column.scale, 
													max=column.cmax,
													min=column.cmin,
													sk=None, # Not doing anything with shared key yet
													descrip=column.description,
													title=column.name
													)

		for rowName, row in self.rows.items():
			for colName, val in row.data.items():
				valCopy = val
				try:
					dmin = columns[colName]['min']
					dmax = columns[colName]['max']
					percentage = ((float(val) - dmin) / (dmax - dmin)) * 100;
					percentage = min(percentage, 100)
					percentage = max(percentage, 0)
				except (ZeroDivisionError,ValueError):
					percentage = 0
				
				try:
					val = columns[colName]['format'].format(val)
				except ValueError:
					try:
						val = columns[colName]['format'].format(float(samp[k]))
					except ValueError:
						val = valCopy
				except:
					val = valCopy
					
				table_html['rows'][rowName][colName] = \
					'<td class="data-coloured {colName}" >\
						<div class="wrapper">\
							<span class="bar" style="width:{percentage}%;"></span>\
							<span class="val">{val}</span>\
						</div>\
					</td>'.format(colName=colName, percentage=percentage, val=val)

		output_html = """
		<div class="table-responsive">
			<table id="general_stats_table" class="table table-condensed mqc_table">
				<thead>
					<tr>
						<th class="rowheader">Sample Name</th>
		"""

		for colHTML in table_html['columns'].values():
			output_html += colHtml

		output_html += """
					</tr>
				</thead>
				<tbody>
		"""  
		for rowName, row in table_html['rows'].items():
			output_html += """ 
						<tr>
							<th class="rowheader" data-original-sn="{rowName}">{rowName}</th>
			""".format(rowName=rowName)

			for colName, colHTML in table_html['columns'].items():
				if colName in row:
					output_html += row[colName]
				else: 
					output_html += '<td class="'+colName+'"></td>'

			output_html += """ 
						</tr>
			"""
		output_html += """
				</tbody>
			</table>
		</div>
		"""
		return output_html