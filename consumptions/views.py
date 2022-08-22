from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from .models import Consumption, WaterConsumption
from .utils import *
from posts.models import Post

# 하루동안 영양소 총합을 보여주는 VIEW
class DayNutrientView(APIView):
  
  def get_post(self, request, date):
    try:
      post = Post.objects.get(author=self.request.user, created_at=date)
      return post
    except Post.DoesNotExist:
      return None

  def get(self, request):
    date = self.request.GET.get('date', None)
    # 존재하지 않는 날짜 쿼리 시 예외처리
    if date is None:
      data = {
        'error_msg' : '올바른 날짜를 입력하세요.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)
    # Date Format 변환
    date = datetime.fromtimestamp(int(date)/1000)
    post = self.get_post(self, date)
    if post is not None:
      # 음식 정보
      food_consumptions = Consumption.objects.filter(post=post.id)
      # 물 정보
      water_consumption = WaterConsumption.objects.get(post=post.id)
      # Queryset to JSON
      day_food_data = food_consumptions.values() # <class 'django.db.models.query.QuerySet'>
      day_water_data = water_consumption # 가져오는 값은 한개뿐임
      print(day_water_data)
      # calculate logic
      sum_day_data = day_calculate(day_food_data, day_water_data)
      return Response(data=sum_day_data) 
    else:
      data = {
        'error_msg' : '해당 날짜에 작성된 포스트가 존재하지 않습니다.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)

# 일주일동안 영양소 총합을 보여주는 View
class WeekNutrientView(APIView):

  def get_all_posts(self, request, date):
    today_date = datetime.fromtimestamp(int(date)/1000)
    a_week_ago = datetime.fromtimestamp((int(date) - 518400000)/1000)
    try:
      post = Post.objects.filter(author=self.request.user, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
      return post
    except Post.DoesNotExist:
      return None

  def get(self, request):
    date = self.request.GET.get('date', None)
    # 존재하지 않는 날짜 쿼리 시 예외처리
    if date is None:
      data = {
        'error_msg' : '올바른 날짜를 입력하세요.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)
    posts = self.get_all_posts(self, date)
    sum_week_data = week_month_calculate(posts) # 쿼리셋 전달 -> 함수 내에서 개별 개체에 대해 역참조!
    # 날짜 출력 확인
    # for elem in posts:
    #   print(elem)
    return Response(data=sum_week_data)

# 한달동안 영양소 총합을 보여주는 View
class MonthNutrientView(APIView):

  def get_all_posts(self, request, date):
    today_date = datetime.fromtimestamp(int(date)/1000)
    a_month_ago = datetime.fromtimestamp((int(date) - 2592000000)/1000)
    try:
      post = Post.objects.filter(author=self.request.user, created_at__lte=today_date, created_at__gte=a_month_ago).order_by('created_at')
      return post
    except Post.DoesNotExist:
      return None

  def get(self, request):
    date = self.request.GET.get('date', None)
    # 존재하지 않는 날짜 쿼리 시 예외처리
    if date is None:
      data = {
        'error_msg' : '올바른 날짜를 입력하세요.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)
    posts = self.get_all_posts(self, date)
    sum_month_data = week_month_calculate(posts) # 쿼리셋 전달 -> 함수 내에서 개별 개체에 대해 역참조!
    # 날짜 출력 확인
    # for elem in posts:
    #   print(elem)
    return Response(data=sum_month_data)

