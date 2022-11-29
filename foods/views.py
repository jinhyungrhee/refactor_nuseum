from django.shortcuts import render
from .models import Food, Supplement
from .serializers import FoodSerializer, SupplementSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

class FoodsView(APIView):

  def get(self, request):
    paginator =PageNumberPagination()
    paginator.page_size = 10
    search_query = request.GET.get("search", None)
    search_type = request.GET.get("type", None)
    if search_type == "supplement": # supplement type (서로 다른 DB로 접근)
      if search_query != None:
        supplements = Supplement.objects.filter(Q(name__icontains=search_query)).order_by('id')
      else:
        supplements = Supplement.objects.all()
      results = paginator.paginate_queryset(supplements, request)
      serializer = SupplementSerializer(results, many=True)
      return paginator.get_paginated_response(data=serializer.data)
    else: # food type (서로 다른 DB로 접근)
      if search_query != None:
        foods = Food.objects.filter(Q(name__icontains=search_query)).order_by('classifier', 'id')
      else: # 쿼리가 없으면 전체 음식 출력
        foods = Food.objects.all()
      results = paginator.paginate_queryset(foods, request)
      serializer = FoodSerializer(results, many=True)
      return paginator.get_paginated_response(data=serializer.data)