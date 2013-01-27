'''
Created on 13 Jan 2013

@author: Rubin
'''

from models import Processor, SMS, Task
from processor import SMSProcessor
from threading import Thread
import device
import time
from mythread import LogExceptionThread
import logging

def add_processor_jobs(sms):
    for processor in Processor.objects.all():
        if processor.receiver == sms.received:
            task = Task()
            task.message = sms
            task.processor = processor
            task.processed = False
            task.save()
    
def send_sms(number, text):
    sms = SMS()
    sms.number = number
    sms.text = text
    sms.state = SMS.STATE_NEW
    sms.received = False
    sms.save()
    add_processor_jobs(sms)
    
def recv_sms():
    new = False
    for message in device.get_message_list():
        number = message.number
        date = message.date
        text = message.text
        if not SMS.objects.filter(date=date, number=number, text=text).exists():
            sms = SMS()
            sms.number = number
            sms.text = text
            sms.date = date
            sms.state = SMS.STATE_NEW
            sms.received = False
            sms.save()
            add_processor_jobs(sms)
            new = True
            message.delete()
    return new

class Receive_Thread(LogExceptionThread):
    def __init__(self):
        super(Receive_Thread, self).__init__()
        self.daemon = True
    def run(self):
        while True:
            if recv_sms():
                logging.info("New SMS received.")
            time.sleep(15)
            
def start_recv_loop():
    recv_thread = Receive_Thread()
    recv_thread.start()
    
def process_pending():
    for sms in SMS.objects.filter(state = SMS.STATE_NEW):
        process_failed = False
        for task in Task.objects.filter(message_id = sms.id, processed = False):
            p = SMSProcessor.create(task.processor)
            result = p.handle(sms)
            if result:
                task.result = result
                task.processed = True
                task.save()
            else:
                process_failed = True
        if not process_failed:
            sms.state = SMS.STATE_PROCESSED
            sms.save()

        

        
