#code from http://loose-bits.com/2010/10/distributed-task-locking-in-celery.html merged with
#code merged with http://ask.github.com/celery/cookbook/tasks.html

from django.conf import settings
from django.core.cache import cache
from django.utils.log import getLogger

def only_one(function=None, key="", timeout=None):
    """Enforce only one celery task at a time."""
    def _dec(run_func):
        """Decorator."""

        def _caller(*args, **kwargs):
            """Caller."""
	    logger = getLogger(**kwargs)
            ret_value = None
	    # cache.add fails if if the key already exists
	    # memcache delete is very slow, but we have to use it to take
	    # advantage of using add() for atomic locking
    	    have_lock = lambda: cache.add(key, "true", timeout)
    	    release_lock = lambda: cache.delete(key)
            try:
                if have_lock():
            	    logger.debug("Lock aquired for task : %s" % key)
                    ret_value = run_func(*args, **kwargs)
            finally:
                if have_lock():
                    release_lock()
            	    logger.debug("Lock released for task : %s" % key)

            return ret_value

        return _caller

    return _dec(function) if function is not None else _dec
