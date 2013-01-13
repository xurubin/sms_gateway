#!/usr/bin/python

import os 
import sys 
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir)) 

from sms_gateway import settings 
from django.core.management import setup_environ 
setup_environ(settings)
