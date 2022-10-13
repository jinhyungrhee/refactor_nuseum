from django.shortcuts import render
from .models import Food
from .serializers import FoodSerializer
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
    # print(search_query)
    if search_query != None:
      foods = Food.objects.filter(Q(name__icontains=search_query)).order_by('classifier', 'id')
    else: # 쿼리가 없으면 전체 음식 출력
      foods = Food.objects.all()
    results = paginator.paginate_queryset(foods, request)
    serializer = FoodSerializer(results, many=True)
    return paginator.get_paginated_response(data=serializer.data)