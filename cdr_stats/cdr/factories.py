from cdr import models

class CDRFactory: # factory class
	@staticmethod
	def get_cdr_app(app_name):
		cdr_app_class = getattr(models, app_name, None)
		if cdr_app_class == None:
			raise ValueError('No CDR app class with name "%s".' % app_name)
		return cdr_app_class()
		
