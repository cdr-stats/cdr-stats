from cdr.models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Customer, Staff


class UserProfileInline(admin.StackedInline):
    model = UserProfile


class StaffAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser', 'last_login')

    def queryset(self, request):
        qs = super(UserAdmin, self).queryset(request)
        qs = qs.filter(Q(is_staff=True) | Q(is_superuser=True))
        return qs

class CustomerAdmin(StaffAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser', 'last_login')

    def queryset(self, request):
        qs = super(UserAdmin, self).queryset(request)
        qs = qs.exclude(Q(is_staff=True) | Q(is_superuser=True))
        return qs
        
    
admin.site.unregister(User)
admin.site.register(Staff, StaffAdmin)
admin.site.register(Customer, CustomerAdmin)


# Setting
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'fax')
    search_fields = ('name', 'phone')

admin.site.register(Company, CompanyAdmin)

# Setting
class CDRAdmin(admin.ModelAdmin):
    list_display = ('id', 'src', 'dst', 'calldate', 'clid', 'channel', 'duration', 'disposition', 'accountcode')
    list_filter = ['calldate', 'accountcode']
    search_fields = ('accountcode', 'dst', 'src')
    ordering = ('-id',)

admin.site.register(CDR, CDRAdmin)


