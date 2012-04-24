.. _conf-example:

Sample Configuration
====================

This is a sample configuration to get you started.
It should contain all you need to create a basic set-up.
 
------------------------
The Configuration Module
------------------------

Some of the more important parts of the configuration module for the Newfies,
``settings.py``, are explained below::

  import os.path
  APPLICATION_DIR = os.path.dirname(globals()['__file__'])

``APPLICATION_DIR`` now contains the full path of your project folder and can be used elsewhere
in the ``settings.py`` module so that your project may be moved around the system without you having to
worry about changing any troublesome hard-coded paths. ::

  DEBUG = True

turns on debug mode allowing the browser user to see project settings and temporary variables. ::

  ADMINS = ( ('xyz', 'xyz@abc.com') )

sends all errors from the production server to the admin's email address. ::

      DATABASE_ENGINE = 'mysql'
      DATABASE_NAME = 'db-name'
      DATABASE_USER = 'user'
      DATABASE_PASSWORD = 'password'
      DATABASE_HOST = 'mysql-host'
      DATABASE_PORT = ''

sets up the options required for Django to connect to your database. ::

     MEDIA_ROOT = os.path.join(APPLICATION_DIR, 'static')

tells Django where to find your media files such as images that the ``HTML
templates`` might use. ::

     ROOT_URLCONF = 'urls'

tells Django to start finding URL matches at in the ``urls.py`` module in the ``newfies`` project folder. ::

      TEMPLATE_DIRS = ( os.path.join(APPLICATION_DIR, 'templates'), )

tells Django where to find your HTML template files. ::

     INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    ...
    'cdr',
    ...
    )

tells Django which applications (custom and external) to use in your project.
The custom applications, ``cdr`` etc. are stored
in the project folder along with these custom applications.




