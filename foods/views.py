from django.shortcuts import render
from .models import Food, Supplement, Efood
from .serializers import FoodSerializer, SupplementSerializer, EnglishFoodSerializer
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
# permission
from rest_framework.permissions import AllowAny
import re

class FoodsView(APIView):

  # permission
  def get_permissions(self):
    permission_classes = [AllowAny]
    return [permission() for permission in permission_classes]

  def get(self, request):
    paginator =PageNumberPagination()
    paginator.page_size = 10
    reg = re.compile(r'[a-zA-Z]')

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
        if reg.match(search_query): # 검색어가 영어
          # 영문 DB에서 검색해서 기존 food DB와 연결
          #print(f'영어 : {search_query}')
          efoods = Food.objects.filter(Q(name__icontains=search_query) & Q(lang='eng')).order_by('classifier')
          results = paginator.paginate_queryset(efoods, request)
          serializer = EnglishFoodSerializer(results, many=True)
        else: # 검색어가 한글
          #print(f'한글 : {search_query}')
          # === 카테고리 추가 (23.03.06) ===
          search_category = request.GET.get("cat", None)
          # ===============================
          if search_category != None:
            foods = Food.objects.filter(Q(name__icontains=search_query) & Q(category__icontains=search_category) & Q(lang='ko')).order_by('classifier', 'id')
          else: # TODO: 프론트엔드 로직 구현 완료되면 삭제 예정
            foods = Food.objects.filter(Q(name__icontains=search_query) & Q(lang='ko')).order_by('classifier', 'id')
          results = paginator.paginate_queryset(foods, request)
          serializer = FoodSerializer(results, many=True)
        return paginator.get_paginated_response(data=serializer.data)
      else: # 쿼리가 없으면 예외처리
        data = {
            "err_msg" : "음식명을 입력해주세요!" 
          }
        return Response(data=data, status=status.HTTP_400_BAD_REQUEST)