from django.urls import path
from . import views

urlpatterns = [
  path('day/', views.DayNutrientView.as_view()),
  path('week/', views.WeekNutrientView.as_view()),
  path('month/', views.MonthNutrientView.as_view()),
]