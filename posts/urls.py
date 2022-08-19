from rest_framework.routers import DefaultRouter
from django.urls import path
from . import views

urlpatterns = [
  path('', views.PostView.as_view()),
  # path('<int:pk>/', views.PostView.as_view()), # GET 메서드에는 pk를 뺐는데 적용이 됐는지 확인 필요!(<int:pk>를 넣으면 PUT만 호출되어야 함)
]