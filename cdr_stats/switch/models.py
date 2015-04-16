from django.db import models
from django_lets_go.utils import Choice
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import UUIDField
import caching.base


# todo: remove first 2 elements from CDR_SOURCE_TYPE
class SWITCH_TYPE(Choice):

    """
    List of switches
    """
    UNKNOWN = 0, _('UNKNOWN')
    # CSV = 1, _('CSV UPLOAD')
    # API = 2, _('API')
    FREESWITCH = 3, _('FREESWITCH')
    ASTERISK = 4, _('ASTERISK')
    YATE = 5, _('YATE')
    KAMAILIO = 6, _('KAMAILIO')
    OPENSIPS = 7, _('OPENSIPS')
    SIPWISE = 8, _('SIPWISE')
    VERAZ = 9, _('VERAZ')
    # change also cdr.models.CDR_SOURCE_TYPE


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
