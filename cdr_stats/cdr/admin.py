from cdr.models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


# Setting
class CDRAdmin(admin.ModelAdmin):
    list_display = ('acctid', 'src', 'dst', 'calldate', 'clid', 'channel', 'duration', 'disposition', 'accountcode')
    list_filter = ['calldate', 'accountcode']
    search_fields = ('accountcode', 'dst', 'src')
    ordering = ('-acctid',)

admin.site.register(CDR, CDRAdmin)


class UserAdmin(UserAdmin):
  list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser', 'accountcode', 'last_login')
  
  def __init__(self,*args,**kwargs):
    super(UserAdmin,self).__init__(*args,**kwargs)
    fields = list(UserAdmin.fieldsets[0][1]['fields'])
    fields.append('accountcode')
    UserAdmin.fieldsets[0][1]['fields']=fields

admin.site.unregister(User)
admin.site.register(User,UserAdmin)

"""

class MyUserAdmin(UserAdmin):
  def __init__(self,*args,**kwargs):
    super(MyUserAdmin,self).__init__(*args,**kwargs)
    fields = list(UserAdmin.fieldsets[0][1]['fields'])
    fields.append('accountcode')
    UserAdmin.fieldsets[0][1]['fields']=fields

#admin.site.unregister(User)
admin.site.register(MyUser,MyUserAdmin)

"""
