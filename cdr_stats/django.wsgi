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


#TODO Replace the environement
site_package_dirs  = glob.glob(here + '/_env/lib/python*/site-packages')
src_dirs = glob.glob(here + '/_env/src/*')

new_sys_path = [here, os.path.join(here, project_name,),]

for dir in site_package_dirs + src_dirs:
    new_sys_path.append(os.path.join(here, dir))

sys.path = new_sys_path + sys.path

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
