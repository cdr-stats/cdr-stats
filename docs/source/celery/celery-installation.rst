.. _celery-installation:

Celery Installation
===================

------
Celery
------

Celery is an asynchronous task queue/job queue based on distributed message
passing. It is focused on real-time operation, but supports scheduling as well.

You can install Celery either via the Python Package Index (PyPI) or from source::

    $ pip install celery


.. _celery-installing-from-source:

Downloading and installing from source
--------------------------------------

To Download the latest version `click here`_.

.. _click here: http://pypi.python.org/pypi/celery/



You can install it by doing the following::

    $ tar xvfz celery-0.0.0.tar.gz

    $ cd celery-0.0.0

    $ python setup.py build

    $ python setup.py install # as root


.. _celery-installing-from-git:

Using the development version
-----------------------------

You can clone the repository by doing the following::

    $ git clone git://github.com/ask/celery.git
