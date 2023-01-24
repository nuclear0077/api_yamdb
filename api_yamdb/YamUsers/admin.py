from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from YamUsers.models import YamUser

admin.site.register(YamUser, UserAdmin)
