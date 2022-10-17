from django.urls import path
from . import views

urlpatterns = [
  # 사용자용
  path('', views.NoticeAPIView.as_view()),
  # 연구진용
  path('post/', views.NoticeAdminCreateAPIView.as_view()),
  path('<int:pk>/', views.NoticeAdminUpdateAPIView.as_view()),
]