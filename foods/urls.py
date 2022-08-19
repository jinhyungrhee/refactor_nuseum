from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
  path('', FoodsView.as_view()),
  path('name/', FoodNameView.as_view()),
]