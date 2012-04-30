#!/usr/bin/env python
import os, sys

from gevent import monkey
monkey.patch_all()

import settings
import django.core.handlers.wsgi
from socketio import SocketIOServer

from django.core.management import setup_environ
setup_environ(settings)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
application = django.core.handlers.wsgi.WSGIHandler()


if __name__ == '__main__':
    print('Listening on http://%s:%s' % (settings.SOCKETIO_HOST,settings.SOCKETIO_PORT))
    # Start up SocketIOServer, a gevent-pywsgi server which maps the url '/socket.io'
    SocketIOServer((settings.SOCKETIO_HOST, settings.SOCKETIO_PORT), application, resource="socket.io").serve_forever()