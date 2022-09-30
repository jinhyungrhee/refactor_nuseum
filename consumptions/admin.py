from django.contrib import admin
from .models import FoodPost, FoodConsumption, FoodImage, SupplementPost, SupplementConsumption, WaterPost

# Register your models here.
admin.site.register(FoodPost)
admin.site.register(FoodConsumption)
admin.site.register(FoodImage)

admin.site.register(SupplementPost)
admin.site.register(SupplementConsumption)

admin.site.register(WaterPost)