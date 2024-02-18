from django.contrib import admin
from django.contrib.auth import get_user_model
from rest_framework.authtoken import models as authtoken_models

from server.authentication.models import ConfirmationCode

# Register your models here.

UserModel = get_user_model()

@admin.register(UserModel)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(ConfirmationCode)
class ConfirmationCodeAdmin(admin.ModelAdmin):
    pass