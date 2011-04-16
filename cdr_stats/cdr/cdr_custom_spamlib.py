from cdr_stats.cdr.models import *
from dilla import spam
import string
import random
import decimal
import logging
import datetime


log = logging.getLogger('dilla')


@spam.strict_handler('cdr.CDR.accountcode')
def spam_cdr_accountcode_field(field):
    return random.randint(10000, 50000)

@spam.strict_handler('cdr.CDR.duration')
def spam_cdr_duration_field(field):
    return random.randint(0, 1000)

@spam.strict_handler('cdr.CDR.disposition')
def spam_cdr_disposition_field(field):
    return random.randint(1, 6)

@spam.strict_handler('cdr.CDR.src')
@spam.strict_handler('cdr.CDR.clid')
@spam.strict_handler('cdr.CDR.dstchannel')
@spam.strict_handler('cdr.CDR.dst')
def spam_cdr_phonenumber_field(field):
    return str(random.randint(640100100, 740800100))

@spam.strict_handler('cdr.CDR.userfield')
@spam.strict_handler('cdr.CDR.lastapp')
@spam.strict_handler('cdr.CDR.uniqueid')
@spam.strict_handler('cdr.CDR.lastdata')
@spam.strict_handler('cdr.CDR.dcontext')
def spam_cdr_empty_field(field):
    return ''

@spam.strict_handler('cdr.CDR.channel')
def spam_cdr_channel_field(field):
    return 'SIP/' + random.choice(string.ascii_letters) + str(random.randint(10000, 50000))

@spam.strict_handler('cdr.CDR.calldate')
def spam_cdr_calldate_field(field):
    random_minutes = random.randint(-1440*5, 0)
    return datetime.datetime.now() + datetime.timedelta(minutes=random_minutes)

@spam.strict_handler('cdr.UserProfile.user')
def random_fk(field='user', limit=None):
    Related = field.rel.to
    log.debug('Trying to find related object: %s' % Related)
    try:
        query = Related.objects.all().order_by('?')
        if field.rel.limit_choices_to:
            log.debug('Field %s has limited choices. \
                    Applying to query.' % field)
            query.filter(**field.rel.limit_choices_to)
        if limit:
            return query[:limit]
        return query[0]
    except IndexError, e:
        log.info('Could not find any related objects for %s' % field.name)
        return None
    except Exception, e:
        log.critical(str(e))


"""
@spam.global_handler('TextField')
def spam_provider_char_field2(field):
    return random.choice(string.ascii_letters)
"""

