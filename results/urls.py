from django.urls import path
from . import views

urlpatterns = [
  # 임시 API
  path('examination/', views.TempExaminationResultView.as_view()),
]