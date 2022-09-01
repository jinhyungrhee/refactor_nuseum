from django.contrib import admin
from .models import Consumption, FoodImage, SupplementConsmption, WaterConsumption

# Register your models here.
admin.site.register(Consumption)
admin.site.register(WaterConsumption)
admin.site.register(FoodImage)
admin.site.register(SupplementConsmption)
