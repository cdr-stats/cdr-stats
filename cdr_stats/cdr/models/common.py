from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User


class Company(models.Model):
    name = models.CharField(max_length=50, blank=False, null=True)
    address = models.TextField(max_length=400, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    fax = models.CharField(max_length=30, blank=True, null=True)
    
    def __unicode__(self):
        return '[%s] %s' %(self.id, self.name)
        
    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        app_label = "Company"
        db_table = "cdr_company"
        
    class Dilla:
        skip_model = True        

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    accountcode = models.PositiveIntegerField(null=True, blank=True)
    company = models.OneToOneField(Company, verbose_name='Company', null=True, blank=True)
    
    class Dilla:
        skip_model = True
        
    class Meta:
        db_table = "cdr_userprofile"
        app_label = 'Profile'


class Customer(User):    
    class Meta:
        proxy = True
        app_label = 'auth'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    class Dilla:
        skip_model = True

class Staff(User):
    class Meta:
        proxy = True
        app_label = 'auth'
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'
    class Dilla:
        skip_model = True
        
    def save(self, **kwargs):
        if not self.pk:
            self.is_staff = 1
            self.is_superuser = 1
        super(Staff, self).save(**kwargs)
