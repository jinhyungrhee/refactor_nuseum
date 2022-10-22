from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

class TempExaminationResultView(APIView):
  def get(self, request):
    user = request.user.username
    if user == 'NPP01':
      data = {
        'user' : user,
        'data' : None
      }
    elif user == 'NPP02' or user == '오이':
      data = {
        'user' : user,
        'data' : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/result/NPP02/2022.10.20+%EC%9D%BC%EB%B0%98%EA%B2%B0%EA%B3%BC%EC%A7%80+(NPP-02+%E3%84%B1%E3%85%8E%E3%84%B9).pdf"
      }
    else :
      data = {
        'user' : user,
        'data' : None
      }
    return Response(data=data)