from django.contrib import admin

from server.health.models import Measures, Fitness


@admin.register(Measures)
class MeasuresAdmin(admin.ModelAdmin):
    pass

@admin.register(Fitness)
class FitnessAdmin(admin.ModelAdmin):
    pass