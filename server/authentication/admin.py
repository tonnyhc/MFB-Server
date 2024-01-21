from django.contrib import admin
from rest_framework.authtoken import models as authtoken_models

# Register your models here.

@admin.register(authtoken_models.Token)
class TokenAdmin(admin.ModelAdmin):
    pass