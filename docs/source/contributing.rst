.. _contributing:

============
Contributing
============

This document is highly inspired from the `Celery`_ documentation.

.. _`Celery`: http://docs.celeryproject.org/en/latest/contributing.html


Welcome to CDR-Stats!

This document is fairly extensive and you are not really expected
to study this in detail for small contributions;

    The most important rule is that contributing must be easy
    and that the community is friendly and not nitpicking on details
    such as coding style.

If you're reporting a bug you should read the Reporting bugs section
below to ensure that your bug report contains enough information
to successfully diagnose the issue, and if you're contributing code
you should try to mimic the conventions you see surrounding the code
you are working on, but in the end all patches will be cleaned up by
the person merging the changes so don't worry too much.

.. contents::
    :local:

.. _community-code-of-conduct:

Community Code of Conduct
=========================

The goal is to maintain a diverse community that is pleasant for everyone.
That is why we would greatly appreciate it if everyone contributing to and
interacting with the community also followed this Code of Conduct.

The Code of Conduct covers our behavior as members of the community,
in any forum, mailing list, wiki, website, Internet relay chat (IRC), public
meeting or private correspondence.

The Code of Conduct is heavily based on the `Ubuntu Code of Conduct`_,
`Celery Code of Conduct`_, and the `Pylons Code of Conduct`_.

.. _`Ubuntu Code of Conduct`: http://www.ubuntu.com/community/conduct
.. _`Pylons Code of Conduct`: http://docs.pylonshq.com/community/conduct.html
.. _`Celery Code of Conduct`: http://docs.celeryproject.org/en/v2.2.5/contributing.html

Be considerate.
---------------

Your work will be used by other people, and you in turn will depend on the
work of others.  Any decision you take will affect users and colleagues, and
we expect you to take those consequences into account when making decisions.
Even if it's not obvious at the time, our contributions to CDR-Stats will impact
the work of others.  For example, changes to code, infrastructure, policy,
documentation and translations during a release may negatively impact
others work.

Be respectful.
--------------

The CDR-Stats community and its members treat one another with respect.  Everyone
can make a valuable contribution to CDR-Stats.  We may not always agree, but
disagreement is no excuse for poor behavior and poor manners.  We might all
experience some frustration now and then, but we cannot allow that frustration
to turn into a personal attack.  It's important to remember that a community
where people feel uncomfortable or threatened is not a productive one.  We
expect members of the CDR-Stats community to be respectful when dealing with
other contributors as well as with people outside the CDR-Stats project and with
users of CDR-Stats.

Be collaborative.
-----------------

Collaboration is central to CDR-Stats and to the larger free software community.
We should always be open to collaboration.  Your work should be done
transparently and patches from CDR-Stats should be given back to the community
when they are made, not just when the distribution releases.  If you wish
to work on new code for existing upstream projects, at least keep those
projects informed of your ideas and progress.  It many not be possible to
get consensus from upstream, or even from your colleagues about the correct
implementation for an idea, so don't feel obliged to have that agreement
before you begin, but at least keep the outside world informed of your work,
and publish your work in a way that allows outsiders to test, discuss and
contribute to your efforts.

When you disagree, consult others.
----------------------------------

Disagreements, both political and technical, happen all the time and
the CDR-Stats community is no exception.  It is important that we resolve
disagreements and differing views constructively and with the help of the
community and community process.  If you really want to go a different
way, then we encourage you to make a derivative distribution or alternate
set of packages that still build on the work we've done to utilize as common
of a core as possible.

When you are unsure, ask for help.
----------------------------------

Nobody knows everything, and nobody is expected to be perfect.  Asking
questions avoids many problems down the road, and so questions are
encouraged.  Those who are asked questions should be responsive and helpful.
However, when asking a question, care must be taken to do so in an appropriate
forum.

Step down considerately.
------------------------

Developers on every project come and go and CDR-Stats is no different.  When you
leave or disengage from the project, in whole or in part, we ask that you do
so in a way that minimizes disruption to the project.  This means you should
tell people you are leaving and take the proper steps to ensure that others
can pick up where you leave off.

.. _reporting-bugs:

Reporting Bugs
==============

Bugs
----

Bugs can always be described to the :ref:`mailing-list`, but the best
way to report an issue and to ensure a timely response is to use the
issue tracker.

1) **Create a GitHub account.**

You need to `create a GitHub account`_ to be able to create new issues
and participate in the discussion.

.. _`create a GitHub account`: https://github.com/signup/free

2) **Determine if your bug is really a bug.**

You should not file a bug if you are requesting support.  For that you can use
the :ref:`mailing-list`, or :ref:`irc-channel`.

3) **Make sure your bug hasn't already been reported.**

Search through the appropriate Issue tracker.  If a bug like yours was found,
check if you have new information that could be reported to help
the developers fix the bug.

4) **Check if you're using the latest version.**

A bug could be fixed by some other improvements and fixes - it might not have an
existing report in the bug tracker. Make sure you're using the latest version.

5) **Collect information about the bug.**

To have the best chance of having a bug fixed, we need to be able to easily
reproduce the conditions that caused it.  Most of the time this information
will be from a Python traceback message, though some bugs might be in design,
spelling or other errors on the website/docs/code.

    A) If the error is from a Python traceback, include it in the bug report.

    B) We also need to know what platform you're running (Windows, OS X, Linux,
       etc.), the version of your Python interpreter, and the version of
       related packages that you were running when the bug occurred.

6) **Submit the bug.**

By default `GitHub`_ will email you to let you know when new comments have
been made on your bug. In the event you've turned this feature off, you
should check back on occasion to ensure you don't miss any questions a
developer trying to fix the bug might ask.

.. _`GitHub`: http://github.com

.. _issue-trackers:

Issue Trackers
--------------

Bugs for a package in the CDR-Stats ecosystem should be reported to the relevant
issue tracker.

* CDR-Stats Core: https://github.com/cdr-stats/cdr-stats/issues/
* Python-Acapela: https://github.com/cdr-stats/python-acapela/issues
* Lua-Acapela: https://github.com/cdr-stats/lua-acapela/issues
* Python-NVD3: https://github.com/areski/python-nvd3/issues

If you are unsure of the origin of the bug you can ask the
:ref:`mailing-list`, or just use the CDR-Stats issue tracker.

.. _versions:

Versions
========

Version numbers consists of a major version, minor version and a release number.
We use the versioning semantics described by semver: http://semver.org.

Stable releases are published at PyPI
while development releases are only available in the GitHub git repository as tags.
All version tags starts with "v", so version 0.8.0 is the tag v0.8.0.

.. _git-branches:

Branches
========

Current active version branches:

* master (http://github.com/cdr-stats/cdr-stats/tree/master)
* 2.19.10 (http://github.com/cdr-stats/cdr-stats/tree/v2.19.10)

You can see the state of any branch by looking at the Changelog:

    https://github.com/cdr-stats/cdr-stats/blob/master/Changelog


Feature branches
----------------

Major new features are worked on in dedicated branches.
There is no strict naming requirement for these branches.

Feature branches are removed once they have been merged into a release branch.

Tags
====

Tags are used exclusively for tagging releases.  A release tag is
named with the format ``vX.Y.Z``, e.g. ``v2.3.1``.
Experimental releases contain an additional identifier ``vX.Y.Z-id``, e.g.
``v3.0.0-rc1``.  Experimental tags may be removed after the official release.

.. _contributing-changes:

Working on Features & Patches
=============================

.. note::

    Contributing to CDR-Stats should be as simple as possible,
    so none of these steps should be considered mandatory.

    You can even send in patches by email if that is your preferred
    work method. We won't like you any less, any contribution you make
    is always appreciated!

    However following these steps may make maintainers life easier,
    and may mean that your changes will be accepted sooner.

Forking and setting up the repository
-------------------------------------

First you need to fork the repository, a good introduction to this
is in the Github Guide: `Fork a Repo`_.

After you have cloned the repository you should checkout your copy
to a directory on your machine:
::

    $ git clone git@github.com:username/cdr-stats.git

When the repository is cloned enter the directory to set up easy access
to upstream changes:
::

    $ cd cdr-stats
    $ git remote add upstream git://github.com/cdr-stats/cdr-stats.git
    $ git fetch upstream

If you need to pull in new changes from upstream you should
always use the :option:`--rebase` option to ``git pull``:
::

    $ git pull --rebase upstream master

With this option you don't clutter the history with merging
commit notes. See `Rebasing merge commits in git`_.
If you want to learn more about rebasing see the `Rebase`_
section in the Github guides.

If you need to work on a different branch than ``master`` you can
fetch and checkout a remote branch like this:
::

    $ git checkout --track -b 3.0-devel origin/3.0-devel

.. _`Fork a Repo`: http://help.github.com/fork-a-repo/
.. _`Rebasing merge commits in git`:
    http://notes.envato.com/developers/rebasing-merge-commits-in-git/
.. _`Rebase`: http://help.github.com/rebase/

.. _contributing-testing:

Running the unit test suite
---------------------------

To run the CDR-Stats test suite you need to install a few dependencies.
A complete list of the dependencies needed are located in
:file:`requirements/test.txt`.

Installing the test requirements:
::

    $ pip install -U -r requirements/test.txt

When installation of dependencies is complete you can execute
the test suite by calling ``py.test``:
::

    $ py.test

Some useful options to :program:`py.test` are:

* :option:`-x`

    Exit instantly on first error or failed test.

* :option:`--ipdb`

    Starts the interactive IPython debugger on errors.

* :option:`-k EXPRESSION`

    Only run tests which match the given substring expression.

* :option:`-v`

    Increase verbose.

If you want to run the tests for a single test file only
you can do so like this:
::

    $ py.test appointment./tests.py

.. _contributing-pull-requests:

Creating pull requests
----------------------

When your feature/bugfix is complete you may want to submit
a pull requests so that it can be reviewed by the maintainers.

Creating pull requests is easy, and also let you track the progress
of your contribution.  Read the `Pull Requests`_ section in the Github
Guide to learn how this is done.

You can also attach pull requests to existing issues by following
the steps outlined here: http://bit.ly/koJoso

.. _`Pull Requests`: http://help.github.com/send-pull-requests/

.. _contributing-coverage:

Calculating test coverage
~~~~~~~~~~~~~~~~~~~~~~~~~

To calculate test coverage you must first install the :mod:`coverage` module.

Installing the :mod:`coverage` module:
::

    $ pip install -U coverage

Code coverage in HTML:
::

    $ nosetests --with-coverage --cover-html

The coverage output will then be located at
:file:`cdr-stats/tests/cover/index.html`.

Code coverage in XML (Cobertura-style):
::

    $ nosetests --with-coverage --cover-xml --cover-xml-file=coverage.xml

The coverage XML output will then be located at :file:`coverage.xml`

.. _contributing-tox:

Running the tests on all supported Python versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is a ``tox`` configuration file in the top directory of the
distribution.

To run the tests for all supported Python versions simply execute:
::

    $ tox

If you only want to test specific Python versions use the ``-e``
option:
::

    $ tox -e py27

Building the documentation
--------------------------

To build the documentation you need to install the dependencies
listed in :file:`requirements/docs.txt`:
::

    $ pip install -U -r requirements/docs.txt

After these dependencies are installed you should be able to
build the docs by running:
::

    $ cd docs
    $ rm -rf .build
    $ make html

Make sure there are no errors or warnings in the build output.
After building succeeds the documentation is available at :file:`.build/html`.

.. _contributing-verify:

Verifying your contribution
---------------------------

To use these tools you need to install a few dependencies. These dependencies
can be found in :file:`requirements/pkgutils.txt`.

Installing the dependencies:
::

    $ pip install -U -r requirements/pkgutils.txt

pyflakes & PEP8
~~~~~~~~~~~~~~~

To ensure that your changes conform to PEP8 and to run pyflakes
execute:
::

    $ flake8 cdr_stats


.. _coding-style:

Coding Style
============

You should probably be able to pick up the coding style
from surrounding code, but it is a good idea to be aware of the
following conventions.

* All Python code must follow the `PEP-8`_ guidelines.

`pep8.py`_ is an utility you can use to verify that your code
is following the conventions.

.. _`PEP-8`: http://www.python.org/dev/peps/pep-0008/
.. _`pep8.py`: http://pypi.python.org/pypi/pep8

* Docstrings must follow the `PEP-257`_ conventions, and use the following
  style.

    Do this:

    .. code-block:: python

        def method(self, arg):
            """Short description.

            More details.

            """

    or:

    .. code-block:: python

        def method(self, arg):
            """Short description."""


    but not this:

    .. code-block:: python

        def method(self, arg):
            """
            Short description.
            """

.. _`PEP-257`: http://www.python.org/dev/peps/pep-0257/

* Lines should not exceed 78 columns.

  You can enforce this in :program:`vim` by setting the ``textwidth`` option:

  .. code-block:: vim

        set textwidth=78

  If adhering to this limit makes the code less readable, you have one more
  character to go on, which means 78 is a soft limit, and 79 is the hard
  limit :)

* Import order

    * Python standard library (`import xxx`)
    * Python standard library ('from xxx import`)
    * Third party packages.
    * Other modules from the current package.

    or in case of code using Django:

    * Python standard library (`import xxx`)
    * Python standard library ('from xxx import`)
    * Third party packages.
    * Django packages.
    * Other modules from the current package.

    Within these sections the imports should be sorted by module name.

    Example:

    .. code-block:: python

        import threading
        import time

        from collections import deque
        from Queue import Queue, Empty

        from .datastructures import TokenBucket
        from .five import zip_longest, items, range
        from .utils import timeutils

* Wildcard imports must not be used (`from xxx import *`).

* For distributions where Python 2.5 is the oldest support version
  additional rules apply:

    * Absolute imports must be enabled at the top of every module::

        from __future__ import absolute_import

    * If the module uses the with statement and must be compatible
      with Python 2.5 then it must also enable that::

        from __future__ import with_statement

    * Every future import must be on its own line, as older Python 2.5
      releases did not support importing multiple features on the
      same future import line::

        # Good
        from __future__ import absolute_import
        from __future__ import with_statement

        # Bad
        from __future__ import absolute_import, with_statement

     (Note that this rule does not apply if the package does not include
     support for Python 2.5)


* Note that we use "new-style` relative imports when the distribution
  does not support Python versions below 2.5

    This requires Python 2.5 or later:

    .. code-block:: python

        from . import submodule

.. _contact_information:

Contacts
========

This is a list of people that can be contacted for questions
regarding the official git repositories, PyPI packages
Read the Docs pages.

If the issue is not an emergency then it is better
to :ref:`report an issue <reporting-bugs>`.


Committers
----------

Areski Belaid
~~~~~~~~~~~~~

:github: https://github.com/areski
:twitter: http://twitter.com/#!/areskib

Website
-------

The CDR-Stats Project is run and maintained by

Star2Billing
~~~~~~~~~~~~

:website: http://star2billing.com/
:twitter: https://twitter.com/#!/star2billing

.. _release-procedure:


Release Procedure
=================

Updating the version number
---------------------------

The version number must be updated one place:

    * :file:`cdr_stats/cdr_stats/__init__.py`

After you have changed these files you must render
the ``README`` files.  There is a script to convert sphinx syntax
to generic reStructured Text syntax, and the make target `readme`
does this for you:
::

    $ make readme

Now commit the changes:
::

    $ git commit -a -m "Bumps version to X.Y.Z"

and make a new version tag:
::

    $ git tag vX.Y.Z
    $ git push --tags

Releasing
---------

Commands to make a new public stable release::

    $ make distcheck  # checks pep8, autodoc index, runs tests and more
    $ make dist  # NOTE: Runs git clean -xdf and removes files not in the repo.
    $ python setup.py sdist bdist_wheel upload  # Upload package to PyPI

If this is a new release series then you also need to do the
following:

* Go to the Read The Docs management interface at:
    http://readthedocs.org/projects/cdr-stats/?fromdocs=cdr-stats

* Enter "Edit project"

    Change default branch to the branch of this series, e.g. ``2.4``
    for series 2.4.

* Also add the previous version under the "versions" tab.

.. _`mailing-list`: https://groups.google.com/forum/#!forum/cdr-stats

.. _`irc-channel`: http://docs.cdr-stats.org/en/latest/getting-started/resources.html#irc

.. _`report an issue`: http://docs.cdr-stats.org/en/latest/contributing.html#reporting-bugs
