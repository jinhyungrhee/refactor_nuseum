from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
# images.json을 통해 이미지 가져오기
from config.settings import get_images

class TempExaminationResultView(APIView):
  def get(self, request):
    user = request.user.username
    data = {
      'user' : user,
      'data' : get_images(user)
    }
    return Response(data=data)