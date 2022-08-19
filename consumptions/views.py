from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from .models import Consumption

# 하루 동안 영양소 총합을 보여주는 VIEW
class DayNutreintView(APIView):
  def get(self, request):
    date = self.request.GET.get('date', None)
    # 존재하지 않는 날짜 쿼리 시 예외처리
    if date is None:
      data = {
        'error_msg' : '올바른 날짜를 입력하세요.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)
    # Date Format 변환
    date = datetime.fromtimestamp(int(date)/1000).strftime("%Y%m%d")
    post = self.get_post(self, date)
    if post is not None:
      consumptions = Consumption.objects.filter(post=post.id)
       # Queryset to JSON
      data = consumptions.values()
      return Response(data=data) 
    else:
      data = {
        'error_msg' : '해당 날짜에 포스트가 존재하지 않습니다.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)