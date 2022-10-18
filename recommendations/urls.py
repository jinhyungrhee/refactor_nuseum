from django.urls import path
from . import views

urlpatterns = [
  # 사용자 API
  # 맞춤식품 목록 확인(LIST)
  path('user/', views.RecommendationUserListView.as_view()),
  path('user/<int:pk>/', views.RecommendationUserDetailView.as_view()),
  # 맞춤식품 상세 확인(DETAIL)
  # 연구원 API
  # 맞춤식품 입력(POST) 및 확인(GET)
  path('admin/', views.RecommendationAdminCreateView.as_view()),
  # 맞춤식품 수정(PATCH) 및 삭제(DELETE)
  path('admin/<int:pk>/', views.RecommendationAdminUpdateView.as_view()),
]