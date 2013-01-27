#!/usr/bin/python
import os 
import sys 
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
    
def server():
    server = ('pi.xurubin.com', 5222)
    peer.init(server) #Nonblocking
    start_recv_loop() #Nonblocking
    controller.run(server) #Block
    
if __name__ == '__main__':
    server()
