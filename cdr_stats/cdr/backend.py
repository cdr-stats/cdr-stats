from django.conf import settings

class BackendNotFound(Exception):
    pass

class BackendNotConfigured(Exception):
    pass


class CDRBackend(object):
    """All Backend Sub-classes to inherit from this and implement the below methods"""
    # The below are optional attributes to be implemented and used by subclases.
    #
    # Application name or some unique identifier for the backend.
    backend_name = ""
        
    def show_cdr(self, *args, **kwargs):
    	'''Must be implemented by subclass'''
        raise NotImplementedError 
        
    def show_graph_by_day(self, *args, **kwargs):
    	'''Must be implemented by subclass'''
        raise NotImplementedError
    
    def show_graph_by_month(self, *args, **kwargs):
    	'''Must be implemented by subclass'''
        raise NotImplementedError 
        
    def show_graph_by_hour(self, *args, **kwargs):
    	'''Must be implemented by subclass'''
        raise NotImplementedError
    
    def show_concurrent_calls(self, *args, **kwargs):
    	'''Must be implemented by subclass'''
        raise NotImplementedError
    
    def show_global_report(self, *args, **kwargs):
    	'''Must be implemented by subclass'''
        raise NotImplementedError
    
    def show_dashboard(self, *args, **kwargs):
    	'''Must be implemented by subclass'''
        raise NotImplementedError 
        
    def export_to_csv(self, *args, **kwargs):
    	'''Must be implemented by subclass'''
        raise NotImplementedError
    

def import_module(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def get_cdr_backend(cdr_platform, *args, **kwargs):
    """Return the relavant backend instance specified by `platform` name"""
    backend_import_file = "cdr.backends.%s" %cdr_platform.lower()
    cdr_backend_classname = "%sBackend" %cdr_platform
    backend_file = None
    
    try:
        backend_file = import_module(backend_import_file)
    except ImportError:
        pass
        
    if not backend_file:
        raise BackendNotFound("Missing %s backend in the CDR module." %cdr_platform)
    
    try:
        backend_class = getattr(backend_file, cdr_backend_classname)
        return backend_class()
    except AttributeError:
        raise BackendNotConfigured("Missing %s class in the %s File." %(cdr_backend_classname, backend_file.__name__))

   
def get_cdr_backend_template(cdr_platform, template_name):
     """Return the relavant backend instance template path based on specified `platform` name"""
     base_template_path = getattr(settings, 'BASE_TEMPLATE_PATH', 'cdr/backends/' )
     cdr_backend_template_path = "%s%s/" %(base_template_path, cdr_platform.lower())
     return "%s%s" %(cdr_backend_template_path, template_name)
 
def get_cdr_backend_model(cdr_platform, *args, **kwargs):
     """Return the relavant model instance specified by `platform` name"""
     pass


def get_cdr_backend_form(cdr_platform, *args, **kwargs):
    """Return the relavant model instance specified by `platform` name"""
    pass
