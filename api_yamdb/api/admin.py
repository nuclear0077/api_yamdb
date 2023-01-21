from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from api_yamdb.api_yamdb.models import YamUser

admin.site.register(YamUser, UserAdmin)
