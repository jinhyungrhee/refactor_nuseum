import imp
from django.contrib import admin
from .models import User, UserSession

# Register your models here.
admin.site.register(User)
# user_session test
admin.site.register(UserSession)