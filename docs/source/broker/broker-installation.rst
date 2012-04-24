.. _broker-installation:

===================
Broker Installation
===================

This document describes the installation of two different Brokers. One is ``Redis``
and second is ``Rabbitmq``. You can install either to work with CDR-Stats.

.. _broker-redis:

-----
Redis
-----

Download Source
---------------

Download : `redis-server_2.0.0~rc2-1_amd64.deb`_.

.. _redis-server_2.0.0~rc2-1_amd64.deb : https://launchpad.net/ubuntu/maverick/amd64/redis-server/2:2.0.0~rc2-1


To install Redis-Server
-----------------------
::

    $ sudo dpkg -i redis-server_2.0.0~rc2-1_amd64.deb

or you can use apt-get
::

    $ apt-get install redis-server

Running Server
--------------
::

    $ redis-server



.. _broker-rabbitmq:

--------
Rabbitmq
--------

RabbitMQ is a complex and sophisticated product.  If you don't need this
level of robustness, then you might want to take a look at Redis - it
installs easily, runs relatively lean, and can be monitored and
maintained without a lot of fuss.

See `Installing RabbitMQ`_ over at RabbitMQ's website.

.. _`Installing RabbitMQ`: http://www.rabbitmq.com/install.html

.. note::

    If you're getting `nodedown` errors after installing and using
    :program:`rabbitmqctl` then this blog post can help you identify
    the source of the problem:

        http://somic.org/2009/02/19/on-rabbitmqctl-and-badrpcnodedown/

Download Source
---------------
http://www.rabbitmq.com/server.html

.. _http://www.rabbitmq.com/server.html: http://www.rabbitmq.com/server.html


Debian APT repository
----------------------

To make use of the RabbitMQ APT repository,

1. Add the following line to your /etc/apt/sources.list
::

   deb http://www.rabbitmq.com/debian/ testing main

.. note::

    The word **testing** in the above line refers to the state of the release of RabbitMQ,
    not any particular Debian distribution. You can use it with Debian stable, testing or unstable,
    as well as with Ubuntu. In the future there will be a stable release of RabbitMQ in the
    repository.

2. (optional) To avoid warnings about unsigned packages, add RabbitMQ's public key to
   your trusted key list using apt-key(8)
   
::

   $ wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc

   $ sudo apt-key add rabbitmq-signing-key-public.asc

3. Run apt-get update.

4. Install packages as usual; for instance,
::

   $ sudo apt-get install rabbitmq-server


.. _rabbitmq-configuration:

Setting up RabbitMQ
-------------------

To use celery we need to create a RabbitMQ user, a virtual host and
allow that user access to that virtual host::

    $ rabbitmqctl add_user myuser mypassword

    $ rabbitmqctl add_vhost myvhost

    $ rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"

See the RabbitMQ `Admin Guide`_ for more information about `access control`_.

.. _`Admin Guide`: http://www.rabbitmq.com/admin-guide.html

.. _`access control`: http://www.rabbitmq.com/admin-guide.html#access-control


.. _rabbitmq-start-stop:

Starting/Stopping the RabbitMQ server
-------------------------------------

To start the server::

    $ sudo rabbitmq-server

you can also run it in the background by adding the :option:`-detached` option
(note: only one dash)::

    $ sudo rabbitmq-server -detached

Never use :program:`kill` to stop the RabbitMQ server, but rather use the
:program:`rabbitmqctl` command::

    $ sudo rabbitmqctl stop

When the server is running, you can continue reading `Setting up RabbitMQ`_.
