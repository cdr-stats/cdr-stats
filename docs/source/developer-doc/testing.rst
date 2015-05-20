.. _testing:

Test Case Descriptions
======================

-----------
Requirement
-----------

**Run/Start Celery**::

    $ /etc/init.d/celery start

or::

    $ python manage.py celeryd -l info

**Run/Start Redis**::

    $ /etc/init.d/redis-server start

----------------
How to Run Tests
----------------

**1. Run Full Test Suit**::

    $ python manage.py test --verbosity=2

**3. Run CDRStatsAdminInterfaceTestCase**::

    $ python manage.py test cdr.CDRStatsAdminInterfaceTestCase --verbosity=2

**4. Run CDRStatsCustomerInterfaceTestCase**::

    $ python manage.py test cdr.CDRStatsCustomerInterfaceTestCase --verbosity=2
