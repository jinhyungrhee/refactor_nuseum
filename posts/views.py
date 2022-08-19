from django.shortcuts import render
from .models import Post
from .serializers import PostSerializer
from consumptions.serializers import ConsumptionSerializer
from consumptions.models import Consumption
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from datetime import datetime

class PostView(APIView):
  # pk로 해당 post 가져오는 함수
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

  def post(self, request):
    # 아무 값도 입력하지 않았을 때 예외처리(400 에러 리턴)
    if request.data['meal'] == []:
      data = {
        'empty_value_error' : '최소 한 끼는 반드시 입력해야 합니다.'
      }
      return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

    # 날짜 변환: unix timestamp string(1660575600000) -> string(20220816)
    request.data['created_at'] = datetime.fromtimestamp(int(request.data['created_at'])/1000).strftime("%Y%m%d")
    
    # 1. postSerializer 통해 역직렬화하여 값을 DB에 저장 -> Post 객체 생성
    serializer = PostSerializer(data=request.data)
    print(serializer)
    if serializer.is_valid():
      post = serializer.save(
        author=request.user
      )
      post_serializer = PostSerializer(post).data
      
      # 2. 포스트가 생성되고 난 뒤에 그 다음에 해당 post id를 가지고 Post_Consumption 테이블 지정
      for elem in request.data['meal']:
        # 방금 생성된 포스트의 pk값 가져오기
        post_id = post_serializer['id']
        # 입력받은 값들을 consumption 객체의 각 필드에 입력
        food_id = elem[0]
        food_amount = elem[1]
        meal_type = elem[2]
        # TODO : 이미지를 올리고 이미지의 url을 저장

        consumption_data = {
          'post' : post_id,
          'food' : food_id,
          'amount' : food_amount,
          'meal_type' : meal_type,
        }

        consumption_serializer = ConsumptionSerializer(data=consumption_data)
        if consumption_serializer.is_valid():
          # consumption 객체 생성
          consumption_serializer.save()
        else:
          return Response(status=status.HTTP_400_BAD_REQUEST, data=consumption_serializer.errors)

      return Response(data=post_serializer, status=status.HTTP_200_OK)
    else:
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
