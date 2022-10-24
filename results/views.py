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
    elif user == 'NPP02' or user == '오이' or user == '사과' or user == 'nuseum':
      data = {
        'user' : user,
        'data' : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/result/NPP02/2022.10.20+%EC%9D%BC%EB%B0%98%EA%B2%B0%EA%B3%BC%EC%A7%80+(NPP-02+%E3%84%B1%E3%85%8E%E3%84%B9).pdf"
      }
    elif user == 'NPP04':
      data = {
        'user' : user,
        'data' : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/result/NPP04/2022.10.20+%EC%9D%BC%EB%B0%98%EA%B2%B0%EA%B3%BC%EC%A7%80+(NPP-04+%E3%85%87%E3%85%85%E3%85%87).pdf"
      }
    elif user == 'NPP05':
      data = {
        'user' : user,
        'data' : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/result/NPP05/2022.10.20+%EC%9D%BC%EB%B0%98%EA%B2%B0%EA%B3%BC%EC%A7%80+(NPP-05+%E3%85%87%E3%85%85%E3%85%88).pdf"
      }
    elif user == 'NPP06':
      data = {
        'user' : user,
        'data' : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/result/NPP06/2022.10.20+%EC%9D%BC%EB%B0%98%EA%B2%B0%EA%B3%BC%EC%A7%80+(NPP-06+%E3%85%8A%E3%85%87%E3%85%88).pdf"
      }
    elif user == 'NPP07':
      data = {
        'user' : user,
        'data' : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/result/NPP07/2022.10.20+%EC%9D%BC%EB%B0%98%EA%B2%B0%EA%B3%BC%EC%A7%80+(NPP-07+%E3%84%B4%E3%85%87%E3%85%8A).pdf"
      }
    elif user == 'NPP08':
      data = {
        'user' : user,
        'data' : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/result/NPP08/2022.10.20+%EC%9D%BC%EB%B0%98%EA%B2%B0%EA%B3%BC%EC%A7%80+(NPP-08+%E3%85%88%E3%85%8E%E3%84%B9).pdf"
      }
    elif user == 'NPP15':
      data = {
        'user' : user,
        'data' : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/result/NPP15/2022.10.20+%EC%9D%BC%EB%B0%98%EA%B2%B0%EA%B3%BC%EC%A7%80+(NPP-15+%E3%85%88%E3%85%85%E3%85%87).pdf"
      }
    else:
      data = {
        'user' : user,
        'data' : None
      }
    return Response(data=data)