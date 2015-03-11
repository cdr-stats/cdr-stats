from django.db import models
from django_lets_go.utils import Choice
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import UUIDField
from cache_utils.decorators import cached
import caching.base


# todo: remove first 2 elements from CDR_SOURCE_TYPE
class SWITCH_TYPE(Choice):

    """
    List of switches
    """
    ASTERISK = 3, _('ASTERISK')
    FREESWITCH = 4, _('FREESWITCH')
    KAMAILIO = 5, _('KAMAILIO')
    YATE = 6, _('YATE')
    OPENSIPS = 7, _('OPENSIPS')


class Switch(caching.base.CachingMixin, models.Model):

    """This defines the Switch

    **Attributes**:

        * ``name`` - Name of switch.
        * ``ipaddress`` - ipaddress

    **Name of DB table**: voip_switch
    """
    name = models.CharField(max_length=100, blank=False,
                            null=True, unique=True)
    ipaddress = models.CharField(max_length=100, blank=False,
                                 null=False, unique=True)
    switch_type = models.IntegerField(choices=SWITCH_TYPE, default=SWITCH_TYPE.FREESWITCH,
                                      max_length=100, null=False)
    key_uuid = UUIDField(auto=True)

    objects = caching.base.CachingManager()

    def __unicode__(self):
        return '[%s] %s' % (self.id, self.ipaddress)

    class Meta:
        verbose_name = _("switch")
        verbose_name_plural = _("switches")
        db_table = "voip_switch"
