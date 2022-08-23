from django.contrib import admin
from .models import Consumption, FoodImage, WaterConsumption

# Register your models here.
admin.site.register(Consumption)
admin.site.register(WaterConsumption)
admin.site.register(FoodImage)