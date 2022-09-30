from django.urls import path
from . import views

urlpatterns = [
  path('', views.QuestionAPIView.as_view()),
  path('<int:pk>/', views.QuestionDetailAPIView.as_view()),
  path('<int:pk>/edit/', views.QuestionUpdateAPIView.as_view()),
  path('<int:pk>/delete/', views.QuestionDeleteAPIView.as_view()),
  path('<int:pk>/answer/', views.AnswerCreateAPIView.as_view()),
  path('answer/<int:pk>/', views.AnswerDetailDeleteAPIView.as_view()),
]