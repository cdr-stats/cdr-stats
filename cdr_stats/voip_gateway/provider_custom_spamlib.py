from voip_gateway.models import *
from dilla import spam
import string
import random
import decimal
import logging
import datetime


log = logging.getLogger('dilla')


@spam.strict_handler('provider.Provider.metric')
def spam_provider_metric_field(field):
    return random.randint(1, 10)


@spam.global_handler('TextField')
def spam_provider_char_field2(field):
    return random.choice(string.ascii_letters)
