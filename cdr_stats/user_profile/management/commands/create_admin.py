# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.template.defaultfilters import slugify


class Command(BaseCommand):
    """
    command to create a new admin user with a random password
    """

    def handle(self, *args, **kwargs):
        first_name = last_name = None
        name, email = settings.ADMINS[0]
        names = name.split(' ')
        if len(names) > 1:
            username = ''.join(
                [c[0].lower() for c in names[:-1]]) + names[-1].lower()
            first_name = names[0]
            last_name = names[-1]
        else:
            username = slugify(name)
        #Overwrite username with admin
        username = 'root'
        password = User.objects.make_random_password(length=14)

        try:
            User.objects.get(username=username)
            print "Admin {} already exists".format(username)
        except User.DoesNotExist:
            u = User.objects.create_user(username, email, password)
            u.is_staff = True
            u.is_superuser = True
            if first_name:
                u.first_name = first_name
            if last_name:
                u.last_name = last_name
            u.save()
            print 'Created admin with username {} and password {}'.format(
                username,
                password
            )
