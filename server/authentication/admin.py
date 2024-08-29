from django.contrib import admin
from django.contrib.auth import get_user_model
from rest_framework.authtoken import models as authtoken_models

from server.authentication.models import ConfirmationCode, Username

# Register your models here.

UserModel = get_user_model()

@admin.register(UserModel)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(ConfirmationCode)
class ConfirmationCodeAdmin(admin.ModelAdmin):
    pass

@admin.register(Username)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'user')