#
# CDR-Stats License
# http://www.cdr-stats.org
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2013 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from user_profile.models import UserProfile, Customer, Staff
from notification.models import Notice
from notification.admin import NoticeAdmin


class UserProfileInline(admin.StackedInline):
    """
    Extenstion of User.
    User's extra details (ex. email, city, country etc...) will be stored in UserProfile
    """
    model = UserProfile


class StaffAdmin(UserAdmin):
    """
    To differentiate staff from all system users
    """
    inlines = [UserProfileInline]

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff',
                    'is_active', 'is_superuser', 'last_login')

    def queryset(self, request):
        qs = super(UserAdmin, self).queryset(request)
        return qs.filter(Q(is_staff=True) | Q(is_superuser=True))


class CustomerAdmin(StaffAdmin):
    """
    To differentiate customers from all system users
    """
    fieldsets = (
        ('', {
            'fields': ('username', 'password', ),
        }),
        (_('Personal info'), {
            #'classes': ('collapse',),
            'fields': ('first_name', 'last_name', 'email', )
        }),
        (_('Permission'), {
            'fields': ('is_active', 'groups', 'user_permissions',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', )
        }),
    )

    inlines = [
        UserProfileInline,
    ]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff',
                    'is_active', 'is_superuser', 'last_login')

    def queryset(self, request):
        qs = super(UserAdmin, self).queryset(request)
        return qs.exclude(Q(is_staff=True) | Q(is_superuser=True))

admin.site.unregister(User)
admin.site.register(Staff, StaffAdmin)
admin.site.register(Customer, CustomerAdmin)


def make_read(self, request, queryset):
    """
    To mark all notifications as read
    It is being used on notification listing as django custom actions
    """
    try:
        queryset.update(unseen=0)
        self.message_user(request, _("notifications are successfully marked as read."))
    except:
        messages.error(request, _("notifications are not marked as read."))
make_read.short_description = _("mark notification as seen")


class NoticeAdmin(NoticeAdmin):
    list_display = ('message', 'recipient', 'sender', 'notice_type', 'added', 'unseen')
    actions = [make_read]

admin.site.unregister(Notice)
admin.site.register(Notice, NoticeAdmin)
