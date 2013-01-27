'''
Created on 20 Jan 2013

@author: Rubin
'''
from sms import Modem, ModemError, encoding
from threading import Lock

device = Modem("/dev/ttyAMA0", 115200)
dlock = Lock()

def get_message_list():
    try:
        dlock.acquire()
        msgs = device.messages()
    except ModemError:
        msgs = device.messages()
    finally:
        dlock.release()
    
    for message in msgs:
        assert message.date
        if not message.number:
            message.number = "Blocked"
        #text = message.text
        #try:
        #    text = encoding.decode_unicode(text)
        #except ValueError:
        #    text = encoding.decode_accents(text)
        #message.text = text.encode('utf-8')
    return msgs

def send_message(number, text):
    try:
        dlock.acquire()
        device.send(number, text)
    finally:
        dlock.release()

def del_message(msg):
    try:
        dlock.acquire()
        msg.delete()
    finally:
        dlock.release()
