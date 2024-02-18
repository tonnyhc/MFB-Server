from django.contrib import admin

from server.health.models import Measures


@admin.register(Measures)
class MeasuresAdmin(admin.ModelAdmin):
    pass
