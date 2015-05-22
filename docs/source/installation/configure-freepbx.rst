
.. _configure-freepbx:

=================
Configure FreePBX
=================

FreePBX is supported by CDR-Stats. CDR-Stats comes with CDR Collector App
called `CDR-Pusher`_, which will be installed on your FreePBX servers to
transport your CDRs to the CDR-Stats server.

CDR-Pusher will be configured to read the `cdr` from SQlite database, which
contains all the Call Data Records. You will need to configure your FreePBX
installation to store CDRs to SQLite for this you can refer to our
Installing on Asterisk documentation :ref:`configure-asterisk`.


.. _`CDR-Pusher`: https://github.com/cdr-stats/cdr-pusher
