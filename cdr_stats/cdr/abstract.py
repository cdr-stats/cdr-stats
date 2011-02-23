

class AbstractCDR(object):

    app_name = ""
    
    def show_cdr(self, **kwargs):
    	'''
    	Must be implemented by subclass.
        '''
        pass  
        
    def show_graph_by_day(self, params):
    	'''
    	Must be implemented by subclass.
        '''
        pass

