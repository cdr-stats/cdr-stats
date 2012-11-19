# -*- coding: utf-8 -*-

from django.conf import settings
from django_socketio import events
from django_socketio.events import on_message
from django.contrib.auth.models import User
from datetime import datetime
from cdr.models import Switch
from django.core.cache import cache
from hashlib import sha256
#import time
#import random
import logging
logger = logging.getLogger('cdr-stats.filelog')


def cached(ctime=3600):
    """
    A `seconds` value of `0` means that we will not memcache it.

    If a result is cached on instance, return that first.
    If that fails, check memcached.
    If all else fails, hit the db and cache on instance and in memcache.
    """

    def decr(func):

        def wrp(*args, **kargs):
            key = sha256(func.func_name + repr(args) + repr(kargs)).hexdigest()
            res = cache.get(key)
            if res is None:
                res = func(*args, **kargs)
                cache.set(key, res, ctime)
            return res

        return wrp

    return decr


@cached(300)  # 5 minutes
def get_switch_id(key_uuid):
    """
    return the switch id
    """
    try:
        switch = Switch.objects.get(key_uuid=key_uuid)
    except:
        return False
    return switch.id


@cached(300)  # 5 minutes
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except:
        return False


@on_message
def my_message_handler(request, socket, context, message):
    logger.debug('In my_message_handler')
    logger.debug(message)
    result = {}
    result['message'] = 'VoIP-Switch'

    key_uuid = message['voipswitch']
    switch_id = get_switch_id(key_uuid)
    if not switch_id:
        logger.debug('Wrong Switch ID')
        result[message['voipswitch']] = 0
        socket.send(result)
        return True

    user = get_user(message['user'])

    if not user:
        logger.debug('Wrong User')
        result[message['voipswitch']] = settings.SOCKETIO_CALLNUM_DEFAULT
        socket.send(result)
        return True

    if not user.is_superuser and (not hasattr(user, 'userprofile')
       or not user.userprofile.accountcode):
        logger.debug('Wrong User')
        result[message['voipswitch']] = settings.SOCKETIO_CALLNUM_DEFAULT
        socket.send(result)
        return True

    now = datetime.today()
    key_date = "%d-%d-%d-%d-%d" % (now.year, now.month, now.day, now.hour, now.minute)

    if not user.is_superuser:
        accountcode = str(user.userprofile.accountcode)
    elif (hasattr(user, 'userprofile') and user.userprofile.accountcode
         and user.is_superuser):
        accountcode = str(user.userprofile.accountcode)
    elif user.is_superuser:
        accountcode = 'root'
    logger.debug(accountcode)

    key = "%s-%d-%s" % (key_date, switch_id, str(accountcode))
    numbercall = cache.get(key)
    logger.debug("key:%s, accountcode:%s, numbercall:%s" % (key, accountcode, str(numbercall)))
    if not numbercall:
        numbercall = 0

    logger.debug('numbercall :::> %d' % numbercall)
    result[message['voipswitch']] = numbercall
    #result[message['voipswitch']] = incr = random.randint(1, 300)
    socket.send(result)


@events.on_message(channel='^switch-')
def message(request, socket, context, message):
    """
    Event handler for a switch receiving a message. First validates a
    joining user's name and sends them the list of users.
    """
    logger.debug('In message')
    logger.debug(message)
    """
    result = {}
    while True:
        time.sleep(1)
        logger.debug('In Loop')
        result["message"] = "We are here..."
        socket.send_and_broadcast_channel(result)
    """
