from django.shortcuts import render
from .models import Food
from .serializers import FoodSerializer, FoodNameSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

class FoodsView(APIView):

  def get(self, request):
    paginator =PageNumberPagination()
    paginator.page_size = 10000
    search_query = request.GET.get("search", None)
    print(search_query)
    if search_query != None:
      foods = Food.objects.filter(Q(name__icontains=search_query)).order_by('classifier')
    else: # 쿼리가 없으면 전체 음식 출력
      foods = Food.objects.all()
    results = paginator.paginate_queryset(foods, request)
    serializer = FoodSerializer(results, many=True)
    return paginator.get_paginated_response(data=serializer.data)

# id를 입력하면 음식명을 리턴하는 메서드 -> deprecated 예정
class FoodNameView(APIView):
  def get(self, request):
    id = request.GET.get('id', None)
    if id != None:
      try:
        food = Food.objects.get(pk=id)
      except Food.DoesNotExist:
        data = {
          'error_msg' : '음식이 존재하지 않습니다.'
        }
        return Response(status=status.HTTP_404_NOT_FOUND, data=data)
    else:
      return Response(status=status.HTTP_404_NOT_FOUND)
    serializer = FoodNameSerializer(food).data
    return Response(serializer)