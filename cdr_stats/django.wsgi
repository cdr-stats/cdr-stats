#!_env/bin/python

"""
WSGI script for usage in Virtalenvs with Apache - Embedded mod_wsgi

Heavily based on
http://blog.dscpl.com.au/2010/03/improved-wsgi-script-for-use-with.html
"""

import glob
import os.path
import sys

here = os.path.abspath(os.path.dirname(__file__))

g = glob.glob(here + '/manage.py')
project_name = os.path.split(g[0])[0]

site_package_dirs = '/usr/share/virtualenvs/cdr-stats/lib/python2.7/site-packages'

if site_package_dirs not in sys.path and os.path.isdir(site_package_dirs):
    sys.path.append(site_package_dirs)

site_package_dirs = '/usr/share/virtualenvs/cdr-stats/lib/python2.6/site-packages'

if site_package_dirs not in sys.path and os.path.isdir(site_package_dirs):
    sys.path.append(site_package_dirs)

sys.path.append('/usr/share/cdrstats')

import settings
import django.core.management

django.core.management.setup_environ(settings)
utility = django.core.management.ManagementUtility()
command = utility.fetch_command('runserver')

command.validate()

import django.conf
import django.utils

django.utils.translation.activate(django.conf.settings.LANGUAGE_CODE)

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
