from django.shortcuts import render
from rest_framework.views import APIView
from .models import Notice
from .serializers import NoticeSerializer, CustomNoticeSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView

# Create your views here.
# 사용자 전용 API
class NoticeAPIView(APIView):

  def get(self, request):
    user = self.request.user.username
    isread = -1

    notices = Notice.objects.all().values()
    fnotices = notices.values('id','title', 'content', 'created_at')

    for i in range(len(fnotices)):
      if f'{user}' in notices[i]['user_list']:
        isread = 1  
      else: 
        isread = 0  
      # setattr(notices[i], str(user), isread)  
      # fnotices[i][str(user)] = isread 
      fnotices[i]['is_read'] = isread # key 변경
      # print(notices[i].NPP01) 

    return Response(data=fnotices)

  def post(self, request):
    if not request.user.is_authenticated:
      return Response(status=status.HTTP_401_UNAUTHORIZED)

    serializer = CustomNoticeSerializer(data=request.data)

    if serializer.is_valid():

    #  mnotices = Notice.objects.get(id=int(*request.data["id"]))
     mnotices = Notice.objects.get(id=request.data["id"])
     check_list = mnotices.user_list[1:].split(".")

     if f'{request.user.username}' in check_list:
       check_list.remove(f'{request.user.username}')
       re_list = ('.'.join(check_list))
       if len(re_list) != 0: re_list = '.'+ re_list
       mnotices.user_list = re_list
     else:
       mnotices.user_list += f'.{request.user.username}'

     mnotices.save()
     
     return Response(data=serializer.data, status=status.HTTP_200_OK)
    else:
      return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 연구원 전용 API
class NoticeAdminCreateAPIView(CreateAPIView):
  queryset = Notice.objects.all()
  serializer_class = NoticeSerializer

class NoticeAdminUpdateAPIView(RetrieveUpdateDestroyAPIView):
  queryset = Notice.objects.all()
  serializer_class = NoticeSerializer
