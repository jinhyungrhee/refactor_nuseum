from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

class TempExaminationResultView(APIView):
  def get(self, request):
    user = request.user.username
    data = {
      'user' : user
    }
    return Response(data=data)
