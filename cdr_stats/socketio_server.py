#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey
monkey.patch_all()

import os
import sys
import logging
import optparse
from daemon import Daemon

import settings
import django.core.handlers.wsgi
from socketio import SocketIOServer

from django.core.management import setup_environ
setup_environ(settings)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
application = django.core.handlers.wsgi.WSGIHandler()

version = 'v1.0'


#setup logger
logger = logging.getLogger("socketio_server")
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler("socketio_server.log")
fh.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s\t%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)


class StdErrWrapper:
    def __init__(self):
        self.logger = logging.getLogger("socketio_server.access")

    def write(self, s):
        self.logger.info(s.rstrip())


class MyDaemon(Daemon):
    def run(self):
        #while True:
        self.logger = logging.getLogger("socketio_server")
        self.logger.info("Creating websocket-server")
        SocketIOServer((settings.SOCKETIO_HOST, settings.SOCKETIO_PORT),
            application, resource="socket.io",
            log=StdErrWrapper()).serve_forever()
        self.logger.info("Done.")


if __name__ == "__main__":
    parser = optparse.OptionParser(usage="usage: %prog -d|c|m [options]",
                    version="CDR-Stats socketio-server " + version)
    parser.add_option("-c", "--config", action="store", dest="config",
                    default="socketio-server.cfg", help="Path to config file",)
    parser.add_option("-d", "--daemon", action="store_true", dest="daemon",
                    default=False, help="Start as daemon",)
    parser.add_option("-m", "--master", action="store_true", dest="master",
                    default=False, help="Start master in foreground",)
    parser.add_option("-p", "--pid", action="store", dest="pid",
                    default="/tmp/socketioserver.pid", help="Path to pid file",)

    (options, args) = parser.parse_args()
    if options.daemon:
        daemon = MyDaemon(options.pid)

        if len(args) != 1:
            parser.error("Hmm... what about action? socketio_server.py -d start|stop|restart")

        if "start" == args[0]:
            daemon.start()
        elif "stop" == args[0]:
            daemon.stop()
        elif "restart" == args[0]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)

    elif options.master:
        print "Starting as master..."
        daemon = MyDaemon(options.pid)
        #daemon.load_config(options.config)
        try:
            daemon.run()
        except KeyboardInterrupt:
            print "\nGot Ctrl-C, shutting down..."
        except Exception, e:
            print "Oops...", e
        print "Bye!"

    else:
        parser.print_usage()
        sys.exit(1)
