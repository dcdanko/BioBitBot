#!/usr/bin/env python

from collections import defaultdict,OrderedDict
from string import strip
import re
import sqlite3 as sql




class SqlDataTableColumnInfo(object):
	def __init__(self, table, name, dataType):
		self.table = table
		self.name = name # Same as 'title' in other parts of the general_stats table
		self.dataType = dataType
		self.description = ''
		self.cmax = float('inf')
		self.cmin = float('-inf')
		self.scale = 'GnBu'
		self.format = '{:.1f}'


class DataTableRow(object):
	'''
	This is quite a hacky way of making storing data from a 
	table. Will migrate to sql or numpy eventually
	'''		
	def __init__(self, table, rowName, rowData, missingVal=None):
		self.table = table
		self.name = rowName
		self.data = rowData
		self.missingVal = missingVal
		self.fillMissingColumnsWithDefault()


	def fillMissingColumnsWithDefault(self):
		for columnInfo in self.table.columns.values():
			colName = columnInfo.name
			if colName not in self.data:
				self.data[colName] = self.missingVal

	def changeElement(self,colname,newVal):
		if colname in self.table.columns.keys():
			self.data[colname] = newVal
		else:
			assert False # TODO real exception


class SqlDataTable(object):

	def __init__(self,name):

		self.name = name

		self.db = sql.connect(':memory:')
		self.initialized = False
		self.colInfo = OrderedDict()

	def initSqlTable(self):
		assert len(self.colInfo) > 0
		cur = self.db.cursor()
		cols = ["{} {}".format(c.name, c.dataType) for c in self.colInfo.values()]
		cols = ', '.join(cols)
		cmd = "CREATE TABLE {} ({})".format(self.name, cols)
		cur.execute(cmd)
		self.db.commit()
		self.initialized = True

	# Inelegant but probably easy to use
	def addColumnInfo(self, colName, dataType,
						descrip=None, 
						cmax=None, 
						cmin=None, 
						scale=None, 
						format=None):
		newColumnInfo = SqlDataTableColumnInfo(self,colName,dataType)
		if descrip:
			newColumnInfo.description = descrip
		if cmax:
			newColumnInfo.cmax = cmax
		if cmin:
			newColumnInfo.cmin = cmin
		if scale:
			newColumnInfo.scale = scale
		if format:
			newColumnInfo.format = format

		self.colInfo[colName] = newColumnInfo

		if self.initialized:
			cur = self.db.cursor()
			cmd = "ALTER TABLE {} ADD {} {};".format(self.name, colName, dataType)
			cur.execute(cmd)
			self.db.commit()


	def addRow(self, row):
		assert self.initialized
		colNames = ', '.join([c.name for c in self.colInfo.values()])
		data = ', '.join(row)

		cur = self.db.cursor()
		cmd = "INSERT INTO {} ({}) VALUES ({});".format(self.name, colNames, data)
		cur.execute(cmd)
		self.db.commit()

	def addManyRows(self, rows):
		assert self.initialized
		colNames = ', '.join([c.name for c in self.colInfo.values()])
		wildcards = ', '.join(['?' for _ in self.colInfo.values()])
		cur = self.db.cursor()
		cmd = "INSERT INTO {} ({}) VALUES ({});".format(self.name, colNames, wildcards)
		cur.executemany(cmd, rows)
		self.db.commit()



	def getTable(self, sqlCmd="SELECT * FROM {table_name}"):
		sqlCmd = sqlCmd.format(table_name=self.name)
		cur = self.db.cursor()
		rows = cur.execute(sqlCmd)
		sqlCmd = sqlCmd.split()
		colNames = sqlCmd[sqlCmd.index('SELECT')+1:sqlCmd.index('FROM')]
		if colNames[0] == '*':
			cols = self.colInfo.values()
		else:
			cols = []
			for cName in colNames:
				cName = cName.strip()
				cName = cName.strip(',')
				cols.append( self.colInfo[cName])

		return cols, rows


	def as_html(self, sqlCmd="SELECT * FROM {table_name}"):
		table_html = {
						'columns': OrderedDict(),
						'rows': defaultdict(lambda:dict())
					}

		cols, rows = self.getTable(sqlCmd=sqlCmd)

		for colInfo in cols[1:]:
			colName = colInfo.name
			rawHTML = 	"""
						<th id="header_{colName}" class="chroma-col {colName}" data-chroma-scale="{scale}" data-chroma-max="{max}" data-chroma-min="{min}" {sk}>
							<span data-toggle="tooltip" title="{descrip}" >{title}</span>
						</th>
						"""
			table_html['columns'][colName] = rawHTML.format(
													colName=colName, 
													scale=colInfo.scale, 
													max=colInfo.cmax,
													min=colInfo.cmin,
													sk=None, # Not doing anything with shared key yet
													descrip=colInfo.description,
													title=colInfo.name
													)
		for row in rows:
			rowName = row[0]
			row = row[1:]
			for cInd, val in enumerate(row):
				cInd += 1
				colName = cols[cInd].name
				valCopy = val
				try:
					dmin = self.colInfo[colName].cmin
					dmax = self.colInfo[colName].cmax
					percentage = ((float(val) - dmin) / (dmax - dmin)) * 100;
					percentage = min(percentage, 100)
					percentage = max(percentage, 0)
				except (ZeroDivisionError,ValueError):
					percentage = 0
				
				try:
					val = self.colInfo[colName]['format'].format(val)
				except ValueError:
					try:
						val = self.colInfo[colName]['format'].format(float(samp[k]))
					except ValueError:
						val = valCopy
				except:
					val = valCopy
				
				rawHTML = 	"""
							<td class="data-coloured {colName}"> 
								<div class="wrapper"> 
									<span class="bar" style="width:{percentage}%;"></span>
									<span class="val">{val}</span>
								</div>
							</td>
							"""
				table_html['rows'][rowName][colName] = rawHTML.format(colName=colName, percentage=percentage, val=val)

		output_html = """
		<div class="table-responsive">
			<table id="{table_name}" class="table table-condensed mqc_table">
				<thead>
					<tr>
						<th class="rowheader">{sample_name}</th>
		""".format(table_name=self.name,sample_name=cols[0].name)

		for colHTML in table_html['columns'].values():
			output_html += colHTML

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
