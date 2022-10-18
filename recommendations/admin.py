from django.contrib import admin
from .models import Recommendation

# Register your models here.
class RecommendationAdmin(admin.ModelAdmin):
  readonly_fields = ('created_at',)

admin.site.register(Recommendation, RecommendationAdmin)