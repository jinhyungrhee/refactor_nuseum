from django.urls import path
from . import views

urlpatterns = [
  path('', views.PostDateView.as_view()),
  path('<int:pk>/', views.PostIdView.as_view()),
  # path('image/', views.model_image_upload), # formdata 방식
]