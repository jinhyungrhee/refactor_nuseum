from django.contrib import admin
from .models import Food, Supplement, Efood

# Register your models here.
admin.site.register(Food)
admin.site.register(Efood)
admin.site.register(Supplement)