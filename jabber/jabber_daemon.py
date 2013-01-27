#!/usr/bin/python

import sys, time
from daemon import Daemon
 
import os 
import sys 
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir)) 

from sms_gateway import settings 
from django.core.management import setup_environ 
setup_environ(settings)

import controller, peer
from main.task import start_recv_loop

from django.db.backends.signals import connection_created
from django.dispatch import receiver

@receiver(connection_created)
def connection_init(sender, connection, **kwargv):
    """ Ensure database consistency between threads """
    connection.cursor().execute("SET autocommit=1")
    
class MyDaemon(Daemon):
    def run(self):
        logging.basicConfig(filename="/home/rubin/sms_gateway/sms_xmpp.log", level=logging.INFO)
        server = ('pi.xurubin.com', 5222)
        logging.info("Starting up: " + str(server))
        peer.init(server) #Nonblocking
        start_recv_loop() #Nonblocking
        controller.run(server) #Block

 
if __name__ == "__main__":
    daemon = MyDaemon('/tmp/sms_xmpp.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
