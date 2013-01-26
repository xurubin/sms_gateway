'''
Created on 20 Jan 2013

@author: Rubin
'''
from sms import Modem, ModemError, encoding

device = Modem("/dev/ttyAMA0", 115200)

def get_message_list():
    try:
        msgs = device.messages()
    except ModemError:
        msgs = device.messages()
        
    for message in msgs:
        assert message.date
        text = message.text
        try:
            text = encoding.decode_unicode(text)
        except ValueError:
            text = encoding.decode_accents(text)
        message = text.encode('utf-8')
    return msgs

def send_message(number, text):
    device.send(number, text)

def del_message(msg):
    msg.delete()