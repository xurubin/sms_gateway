from django.db import models

class SMS(models.Model):
    STATE_NEW        = "new"
    STATE_PROCESSED  = "dealt"
    STATE_ARCHIVED   = "archived"
    MESSAGE_STATE = (
        (STATE_NEW, "New"),
        (STATE_PROCESSED, "Processed"),
        (STATE_ARCHIVED, "Archived")
    )
    date   = models.DateTimeField()
    number = models.CharField(max_length=32)
    text   = models.TextField()
    state  = models.CharField(max_length=8, choices = MESSAGE_STATE) 
    received = models.BooleanField()

class Processor(models.Model):
    receiver = models.BooleanField()
    endpoint = models.TextField()

class Task(models.Model):
    message  = models.ForeignKey(SMS)
    processor = models.ForeignKey(Processor)
    create_date = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField()
    result = models.TextField()
