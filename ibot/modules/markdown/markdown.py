from ibot.modules.base_module import BaseIBotModule
import markdown2

class IBotModule(BaseIBotModule):

	def __init__(self,name='Markdown'):
		super(IBotModule,self).__init__(
						name=name, 
						anchor='_'.join(name.lower().split(' ')),
						info='')

		self.intro += ""


	def buildChartSet(self,text):
		self.intro += markdown2.markdown(text)
