from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView, RetrieveDestroyAPIView, RetrieveUpdateAPIView, CreateAPIView
from rest_framework import status
from .serializers import FoodPostSerializer, FoodConsumptionSerializer, FoodPostImageSerializer, SupplementPostSerializer, SupplementConsumptionSerializer ,WaterSerializer, FoodAdminConsumptionSerializer, FoodAdminImageSerializer, ImageDecodeSerializer
from .models import FoodPost, FoodImage, FoodConsumption, SupplementPost, SupplementConsumption, WaterPost
from datetime import datetime, timedelta
from .permissions import IsOwnerorAdmin
from .utils import convert_to_int_date, count_reporting_date, nutrient_calculator, create_image_url, delete_image
from consumptions import serializers
from accounts.models import User
from accounts.serializers import UserListSerializer
from collections import defaultdict, OrderedDict
import copy
import json

MEAL_TYPE_LIST = ['breakfast', 'lunch', 'dinner', 'snack']
# 카테고리 리스트 추가(23.03.22)
CATEGORY_MAPPER = { '채소':1, '채소류':1, '샐러드':1, '나물':1, '과일':2, '과일류':2, '두부':3, '콩/두부':3, '두류':3, '두유':3, 
                   '메주':3, '된장':3, '통곡물':4, '버섯':5, '버섯류':5, '해조류':6, '견과':7, '견과류':7, '고기/생선/달걀':8, 
                   '육류':8, '난류':8, '수산물':8, '어패류':8, '회류':8, '우유':9, '치즈':9, '유제품':9, '발효유':9, '가공유':9, 
                   '가공두유':9, '보충제':0 }

# FOOD
# FOOD(TYPE&DATE) LIST
# FOOD(IMAGE&CONSUMPTION) CREATE
class FoodPostCreateAPIView(ListCreateAPIView):
  queryset = FoodPost.objects.all()
  serializer_class = FoodPostSerializer

  # Type과 Date를 쿼리 파라미터로 입력받는 API
  def get(self, request, *args, **kwargs):
        type = request.GET.get("type", None)
        date = request.GET.get('date', None)
        # 에러 처리 (date는 무조건 13자리여야함!)
        if type == None or date == None:
          data = {
            'err_msg' : '날짜와 식사 유형이 제대로 입력되지 않았습니다.'
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        # 예외 처리 (date=abcdefghijklm인 경우)
        int_date = convert_to_int_date(date)
        if int_date is None:
          data = {
            'err_msg' : '올바른 date 값을 입력하세요!'
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        
        date_data = datetime.fromtimestamp(int_date/1000)
        queryset = FoodPost.objects.filter(type=type, created_at=date_data, author=self.request.user) # post 입력 순서대로 정렬해서 보여줄 필요성?
        # print(queryset)
        return self.list(request, queryset, *args, **kwargs)

  def list(self, request, queryset, *args, **kwargs):

        if queryset.exists():
          consumption_list = []
          image_list = []
          for i in range(len(queryset)):
            # food_image = FoodImage.objects.filter(post=queryset[i].id).values()
            food_image_serializer = FoodPostImageSerializer(instance=queryset[i].foodimage_set.all(), many=True)
            # print(f"IMAGE : {food_image_serializer.data}")
            food_serializer = FoodConsumptionSerializer(instance=queryset[i].foodconsumption_set.all(), many=True)
            # print(f"CONSUMPTION : {food_serializer.data}")
            consumption_list.extend(food_serializer.data)
            image_list.extend(food_image_serializer.data)

          # 카테고리 리스트 추가(23.03.22)
          category_list = set([])
          for elem in consumption_list:
            for index, (key, val) in enumerate(CATEGORY_MAPPER.items()):
              if key in elem.get('category'):
                category_list.add(val)

          food_data = {
            'type' : queryset[0].type,
            'created_at' : queryset[0].created_at,
            'updated_at' : queryset[0].updated_at,
            'author' : queryset[0].author.id,
            'data' : consumption_list,
            'images' : image_list,
            'category' : category_list, # 카테고리 리스트 추가(23.03.22)
          }
        else:
          food_data = []
        return Response(data=food_data)

  def create(self, request, *args, **kwargs):
        # 예외처리 : 이상한 값 입력 시 예외처리
        try:
          image_list = request.data['images']
          consumption_list = request.data['consumptions']
          meal_type = request.data['type']
          created_at = request.data['created_at']
        except KeyError:
          data = {
            'err_msg' : "입력한 JSON이 올바른 형태인지 확인해주세요 (fields: images, consumptions, type, created_at(unix time))"
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        # 예외처리 : Food 입력 시 images나 consumptions 둘 중 하나는 반드시 있어야 함!(빈 POST 생성 방지!)
        if image_list == [] and consumption_list == []:
          data = {
            "err_msg" : "음식 정보나 음식 이미지 둘 중 하나는 반드시 입력해야 합니다!" 
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        # 예외처리
        if meal_type not in MEAL_TYPE_LIST:
          data = {
            "err_msg" : "type은 반드시 breakfast, lunch, dinner, snack 중 하나여야 합니다!" 
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        date_data = datetime.fromtimestamp(int(created_at)/1000)

        # TODO : S3 이미지 객체 생성 및 AWS_URL 생성 필요 -> image_list 사용 (bulk_create 활용?)        
        '''
        # print(image_list):

        [{"image":"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAeAB4AAD/4RDmRXhpZ..."}, 
        {"image":"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAeAB4AAD/4RDmRXhpZ..."}, 
        {"image":"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAeAB4AAD/4RDmRXhpZ..."}]

        ->

        [{"image" : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/2022/12/01/10_breakfast_0.jpeg"},
        {"image" : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/2022/12/01/10_breakfast_1.jpeg"},
        {"image" : "https://s3.ap-northeast-2.amazonaws.com/jinhyung.test.aws/2022/12/01/10_breakfast_2.jpeg"}]

        for i in range(len(image_list)):
          aws_url = create_image_url(image_list[i]["image"])
          image_list[i]["image"] = aws_url
        
        또는 

        Bulk Create?
        '''
        # image_list 개수만큼 빈칸으로 임시 url 저장
        blank_image_list = [{"image": ""} for _ in range(len(image_list))]
        print(f"BLANK_IMAGE_LIST : {blank_image_list}")

        data = {
          "type" : meal_type,
          "created_at" : date_data,
          "author" : self.request.user.id,
          "images" : blank_image_list,
          "consumptions": consumption_list,
        }
        # serializer = self.get_serializer(data=request.data)
        serializer = self.get_serializer(data=data)
        # print(f"serializer check : {serializer}")
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # ** s3, aws_url 생성후 image 객체 update **
        print(f"IMAGE TEST : {serializer.data['images']}")
        # image_decode_serializer = ImageDecodeSerializer(data=image_list, context={'request':request, 'images':image_list, 'meal_type':meal_type, 'date':date_data})
        # image_decode_serializer = ImageDecodeSerializer(data=serializer.data['images'], context={'request':request, 'images':image_list, 'meal_type':meal_type, 'date':date_data}, many=True)
        # image_decode_serializer = ImageDecodeSerializer(data=serializer.data['images'], context={'request':request, 'meal_type':meal_type, 'date':date_data}, many=True)
        image_object_list = serializer.data['images']
        for i in range(len(image_object_list)):
          image_decode_serializer = ImageDecodeSerializer(data=image_object_list[i], context={'request':request, 'meal_type':meal_type, 'date':date_data, 'image_string':image_list[i]['image'], 'image_id':image_object_list[i]['id'], 'post':image_object_list[i]['post']})
          if image_decode_serializer.is_valid():
            image_decode_serializer.save()
          # print(image_decode_serializer.data)
        headers = self.get_success_headers(serializer.data)
        print(f"최종 SERIALZIER.DATA : {serializer.data}") # 
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

# FOOD CONSUMPTION EDIT/DELETE
class FoodConsumptionUpdateAPIView(RetrieveUpdateDestroyAPIView):
  queryset = FoodConsumption.objects.all()
  serializer_class = FoodConsumptionSerializer

  def get_permissions(self):
    permission_classes = [IsOwnerorAdmin]
    return [permission() for permission in permission_classes]

# FOOD IMAGE DELETE
class FoodImageDeleteAPIView(RetrieveDestroyAPIView):
  queryset = FoodImage.objects.all()
  serializer_class = FoodPostImageSerializer

  def get_permissions(self):
    permission_classes = [IsOwnerorAdmin]
    return [permission() for permission in permission_classes]

  # TODO : DELETE시 S3 이미지 객체도 삭제되도록 구현
  # TODO : DELETE 로직에서 S3 객체 삭제 로직 구현 필요
  def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

  def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # s3 인스턴스 삭제
        delete_image(instance.image)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

  def perform_destroy(self, instance):
      instance.delete()

# SUPPLEMENT
# SUPPLEMENT CREATE
class SupplementCreateAPIView(ListCreateAPIView):
  queryset = SupplementPost.objects.all()
  # serializer_class = SupplementSerializer
  serializer_class = SupplementPostSerializer


  # GET : 날짜를 query parameter로 받아, 해당 날짜의 supplement 보여주는 api(GET)
  def get(self, request, *args, **kwargs):
        date = request.GET.get('date', None)
        int_date = convert_to_int_date(date)
        if int_date is None:
          data = {
            'err_msg' : '올바른 date 값을 입력하세요!'
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        date_data = datetime.fromtimestamp(int_date/1000)
        supplement_queryset = SupplementPost.objects.filter(created_at=date_data, author=self.request.user)
        return self.list(request, supplement_queryset, *args, **kwargs)

  def list(self, request, supplement_queryset, *args, **kwargs):
        print(supplement_queryset)
        if not supplement_queryset.exists():
          # TEST VERSION (admin) 
          # queryset = self.filter_queryset(self.get_queryset())
          # # DEPLOY VERSION (user)
          queryset = [] 
        else:
          # queryset = supplement_queryset
          supplement_consumption_list = []
          for i in range(len(supplement_queryset)):
            food_serializer = SupplementConsumptionSerializer(instance=supplement_queryset[i].supplementconsumption_set.all(), many=True)
            # print(f"CONSUMPTION : {food_serializer.data}")
            supplement_consumption_list.extend(food_serializer.data)

          queryset = {
            'type' : supplement_queryset[0].type,
            'created_at' : supplement_queryset[0].created_at,
            'updated_at' : supplement_queryset[0].updated_at,
            'author' : supplement_queryset[0].author.username,
            'consumptions' : supplement_consumption_list
          }
          print(queryset)
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)

        # serializer = self.get_serializer(queryset, many=True)
        # return Response(serializer.data)
        return Response(data=queryset)

  # POST
  def create(self, request, *args, **kwargs):
        # 예외처리 : 이상한 값 입력 시 예외처리
        try:
          type = request.data['type']
          # name = request.data['name']
          # manufacturer = request.data['manufacturer']
          # image = request.data['image']
          consumption_list = request.data['consumptions']
          created_at = request.data['created_at']
        except KeyError:
          data = {
            # 'err_msg' : "입력한 JSON이 올바른 형태인지 확인해주세요 (fields: type, name, manufacturer, image, created_at(unix time))"
            'err_msg' : "입력한 JSON이 올바른 형태인지 확인해주세요 (fields: type, created_at(unix time), consumptions)"
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        # 예외처리 : type 확인
        if type != "supplement":
          data = {
            "err_msg" : "type은 반드시 supplement이어야 합니다!" 
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        # 예외처리 : 이름, 제조사 반드시 입력 필요!
        # if name == "" or manufacturer == "":
        #   data = {
        #     "err_msg" : "영양제 이름과 제조사명은 반드시 입력해야 합니다!" 
        #   }
        #   return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        date_data = datetime.fromtimestamp(int(created_at)/1000)
        
        # base64 -> s3 url (일단 이미지 추출 후 빈 string으로 대체)
        base64_list = []
        for i in range(len(consumption_list)):
          base64_list.append(consumption_list[i]['image'])
          consumption_list[i]['image'] = ""
          # SupplementConsumptionSerializer(data=consumption_list[i])


        data = {
          "type" : type,
          "created_at" : date_data,
          # "name" : name,
          # "manufacturer" : manufacturer,
          # "image" : "",
          "consumptions" : consumption_list,
          "author" : self.request.user.id,
          # supplement 추가해야하나?
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # image_url = create_image_url(image, serializer.data['id'], date_data, self.request.user.username)
        # serializer.data['image'] = image_url
        # base64 -> s3 url
        for i in range(len(base64_list)):
          image_id = serializer.data['consumptions'][i]['id']
          if base64_list[i] == "":
            continue
          image_url = create_image_url(base64_list[i], image_id, date_data, self.request.user.username)
          supplement_consumption = SupplementConsumption.objects.get(id=image_id)
          supplement_consumption.image = image_url
          supplement_consumption.save()
          serializer.data['consumptions'][i]['image'] = image_url

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class SupplementUpdateAPIView(RetrieveUpdateDestroyAPIView):
  # queryset = SupplementPost.objects.all()
  # serializer_class = SupplementSerializer
  # queryset = SupplementPost.objects.all()
  # serializer_class = SupplementSerializer
  queryset = SupplementConsumption.objects.all()
  serializer_class = SupplementConsumptionSerializer
  # 주의 : 프론트에서 image 필드에 대한 접근은 못하도록 제어 필요!
  # 예외처리 : 작성글(pk)에는 본인만 접근 가능하도록 예외처리!
  def get_permissions(self):
    permission_classes = [IsOwnerorAdmin]
    return [permission() for permission in permission_classes]

  # TODO : DELETE 로직에서 S3 객체 삭제 로직 구현 필요
  def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

  def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # s3 인스턴스 삭제
        if instance.image != "":
          delete_image(instance.image)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

  def perform_destroy(self, instance):
      instance.delete()

# WATER
# WATER CREATE
class WaterCreateAPIView(ListCreateAPIView):
  queryset = WaterPost.objects.all()
  serializer_class = WaterSerializer

  # GET : 날짜를 query parameter로 받아, 해당 날짜의 supplement 보여주는 api(GET)
  def get(self, request, *args, **kwargs):
        date = request.GET.get('date', None)
        int_date = convert_to_int_date(date)
        if int_date is None:
          data = {
            'err_msg' : '올바른 date 값을 입력하세요!'
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        date_data = datetime.fromtimestamp(int_date/1000)
        supplement_queryset = WaterPost.objects.filter(created_at=date_data, author=self.request.user)
        return self.list(request, supplement_queryset, *args, **kwargs)

  def list(self, request, supplement_queryset, *args, **kwargs):
        if supplement_queryset == None:
          # TEST VERSION (admin) 
          queryset = self.filter_queryset(self.get_queryset()) 
          # # DEPLOY VERSION (user)
          # queryset = [] 
        else:
          queryset = supplement_queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

  # POST
  def create(self, request, *args, **kwargs):
        # 예외처리 : 이상한 값 입력 시 예외처리
        try:
          type = request.data['type']
          amount = request.data['amount']
          created_at = request.data['created_at']
        except KeyError:
          data = {
            'err_msg' : "입력한 JSON이 올바른 형태인지 확인해주세요 (fields: type, amount, created_at(unix time))"
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        # 예외처리 : amount 반드시 입력 필요!
        if amount == "":
          data = {
            "err_msg" : "수분량(amount) 값은 반드시 입력해야 합니다!" 
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
        # 예외처리 : type 확인
        if type != "water":
          data = {
            "err_msg" : "type은 반드시 water이어야 합니다!" 
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        date_data = datetime.fromtimestamp(int(created_at)/1000)
        # 예외처리 : 해당 날짜에 WaterPost가 이미 존재하면 에러 리턴
        if WaterPost.objects.filter(author=self.request.user, created_at=date_data).exists():
          data = {
            "err_msg" : "해당 날짜에 이미 생성된 수분 데이터(WaterPost)가 존재합니다!" 
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        data = {
          "type" : type,
          "created_at" : date_data,
          "amount" : amount,
          "author" : self.request.user.id,
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
  
class WaterUpdateAPIView(RetrieveUpdateAPIView):
  queryset = WaterPost.objects.all()
  serializer_class = WaterSerializer

  def get_permissions(self):
    permission_classes = [IsOwnerorAdmin]
    return [permission() for permission in permission_classes]

# TODAY(오늘 탭)
class TodayView(APIView):

  def get(self, request):
    date = self.request.GET.get('date', None)
    int_date = convert_to_int_date(date)
    if int_date is None:
      data = {
        'err_msg' : '올바른 date 값을 입력해주세요!'
      }
      return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
    
    date_data = datetime.fromtimestamp(int_date/1000)
    author = self.request.user

    breakfast_posts = FoodPost.objects.filter(author=author, type='breakfast', created_at=date_data)
    lunch_posts = FoodPost.objects.filter(author=author, type='lunch', created_at=date_data)
    dinner_posts = FoodPost.objects.filter(author=author, type='dinner', created_at=date_data)
    snack_posts = FoodPost.objects.filter(author=author, type='snack', created_at=date_data)

    # BREAKFAST
    breakfast_consumptions = []
    breakfast_images = []

    for i in range(len(breakfast_posts)):
      
      breakfast_serializer = FoodConsumptionSerializer(instance=breakfast_posts[i].foodconsumption_set.all(), many=True)
      breakfast_image_serializer = FoodPostImageSerializer(instance=breakfast_posts[i].foodimage_set.all(), many=True)
      breakfast_consumptions.extend(breakfast_serializer.data)
      breakfast_images.extend(breakfast_image_serializer.data)
      
    breakfast_data = {
      "data" : breakfast_consumptions,
      "image" : breakfast_images
    }

    # LUNCH
    lunch_consumptions = []
    lunch_images = []
    
    for i in range(len(lunch_posts)):
      '''
      lunch_consumption = FoodConsumption.objects.filter(post=lunch_posts[i]).values()
      lunch_image = FoodImage.objects.filter(post=lunch_posts[i]).values()

      if lunch_consumption.exists():
        # lunch_consumptions.append(lunch_consumption)
        lunch_consumptions.extend(lunch_consumption)
      if lunch_image.exists():
        # lunch_images.append(lunch_image)
        lunch_images.extend(lunch_image)
      '''
      lunch_serializer = FoodConsumptionSerializer(instance=lunch_posts[i].foodconsumption_set.all(), many=True)
      lunch_image_serializer = FoodPostImageSerializer(instance=lunch_posts[i].foodimage_set.all(), many=True)
      lunch_consumptions.extend(lunch_serializer.data)
      lunch_images.extend(lunch_image_serializer.data)
      
    lunch_data = {
      "data" : lunch_consumptions,
      "image" : lunch_images
    }
    
    # DINNER
    dinner_consumptions = []
    dinner_images = []
    
    for i in range(len(dinner_posts)):
      
      dinner_serializer = FoodConsumptionSerializer(instance=dinner_posts[i].foodconsumption_set.all(), many=True)
      dinner_image_serializer = FoodPostImageSerializer(instance=dinner_posts[i].foodimage_set.all(), many=True)
      dinner_consumptions.extend(dinner_serializer.data)
      dinner_images.extend(dinner_image_serializer.data)
        
    dinner_data = {
      "data" : dinner_consumptions,
      "image" : dinner_images
    }

    # SNACK
    snack_consumptions = []
    snack_images = []
    
    for i in range(len(snack_posts)):
      
      snack_serializer = FoodConsumptionSerializer(instance=snack_posts[i].foodconsumption_set.all(), many=True)
      snack_image_serializer = FoodPostImageSerializer(instance=snack_posts[i].foodimage_set.all(), many=True)
      snack_consumptions.extend(snack_serializer.data)
      snack_images.extend(snack_image_serializer.data)
        
    snack_data = {
      "data" : snack_consumptions,
      "image" : snack_images
    }

    # supplement
    # supplement_data = list(SupplementPost.objects.filter(author=author, type='supplement', created_at=date_data).values())
    supplement_consumptions = []
    supplement_post = SupplementPost.objects.filter(author=author, type='supplement', created_at=date_data)
    for i in range(len(supplement_post)):
      supplement_consumptions.extend(supplement_post[i].supplementconsumption_set.all().values())
    # print(supplement_consumptions)

    # water
    water_data = WaterPost.objects.filter(author=author, type='water', created_at=date_data).values()

    today_data = {
      'breakfast' : breakfast_data,
      'lunch' : lunch_data,
      'dinner' : dinner_data,
      'snack' : snack_data,
      # 'supplement' : supplement_data,
      'supplement' : supplement_consumptions,
      'water' : water_data
    }
    # print(today_data)

    return Response(data=today_data)

# 식이분석
# DAY : 하루 섭취 영양소 총합
class DayNutrientView(APIView):
  
  def get(self, request):
    date = self.request.GET.get('date', None)
    # 존재하지 않는 날짜 쿼리 시 예외처리
    int_date = convert_to_int_date(date)
    if int_date is None:
      data = {
        'error_msg' : '올바른 날짜를 입력하세요.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)
    # Date Format 변환
    date = datetime.fromtimestamp(int_date/1000)
    # 아침/점심/저녁/간식 영양소
    # 여기에 걸려있는 consumption 객체 다 가져오기 
    food_posts = list(FoodPost.objects.filter(author=request.user, created_at=date).values('id'))
    # print(food_posts)
    day_food_data = FoodConsumption.objects.none() # 빈 쿼리셋 생성
    for i in range(len(food_posts)):
      day_food_data |= FoodConsumption.objects.filter(post=food_posts[i]['id'])
    # print(f"DAY FOOD DATA : {day_food_data}")
    # '''TEST''' => 계산하는 함수에서 이런식으로 계산하면 될 듯!
    '''
    for elem in day_food_data:
      print(elem.food.protein)
    '''
    # 물 정보 가져오기
    day_water_data = WaterPost.objects.filter(author=request.user, created_at=date)
    # print(f"DAY WATER DATA : {day_water_data}") 
    # print(f"DAY WATER DATA : {day_water_data[0].amount}") # 없으면 Index Error 발생!
    # 영양제 정보 가져오기
    supplement_posts = SupplementPost.objects.filter(author=request.user, created_at=date)
    # 수정
    day_supplement_data = SupplementConsumption.objects.none() # 빈 쿼리셋 생성
    for i in range(len(supplement_posts)):
      day_supplement_data |= supplement_posts[i].supplementconsumption_set.all()
    # log
    # print(day_supplement_data)

    reporting_date = count_reporting_date(date, request.user, "day")
    sum_day_data = nutrient_calculator(day_food_data, day_supplement_data, day_water_data, reporting_date)
    # print(sum_day_data)
    return Response(data=sum_day_data)


# WEEK : 일주일 섭취 영양소 총합
class WeekNutrientView(APIView):
  # 섭취한 날짜 계산할 때 '체크' 방법 생각해보기...!
  # FoodPost.objects.filter(author=request.user, created_at=date) # 하나도 없으면 Queryset<[]> 리턴, snack 하나라도 있으면 Queryset<[{,,,}]> 리턴
  # for문을 돌면서 not exist(): 로 count
  # 일주일 - count / 한달 - count로 날짜 수 리턴
  def get(self, request):
    date = self.request.GET.get('date', None)
    today_date = datetime.fromtimestamp(int(date)/1000)
    a_week_ago = datetime.fromtimestamp((int(date) - 518400000)/1000)
    week_food_posts = FoodPost.objects.filter(author=self.request.user, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    week_food_data = FoodConsumption.objects.none() # 빈 쿼리셋
    for i in range(len(week_food_posts)):
      week_food_data |= week_food_posts[i].foodconsumption_set.all()
    # print(week_food_data)
    # week_supplement_data = SupplementPost.objects.filter(author=self.request.user, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    # TODO : supplement 데이터 쿼리셋 만들어서 보내기
    week_supplement_posts = SupplementPost.objects.filter(author=self.request.user, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    week_supplement_data = SupplementConsumption.objects.none() # 빈 쿼리셋 생성
    for i in range(len(week_supplement_posts)):
      week_supplement_data |= week_supplement_posts[i].supplementconsumption_set.all()
    # log
    # print(week_supplement_data)

    week_water_data = WaterPost.objects.filter(author=self.request.user, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    # print(week_food_data)
    # 기록 날짜 체크(today_date, author)
    # decreasing_date = today_date
    reporting_date = count_reporting_date(today_date, request.user, "week")
    sum_week_data = nutrient_calculator(week_food_data, week_supplement_data, week_water_data, reporting_date)
    # print(sum_week_data)
    return Response(data=sum_week_data)


# MONTH : 월 섭취 영양소 총합
class MonthNutrientView(APIView):
  def get(self, request):
    date = self.request.GET.get('date', None)
    today_date = datetime.fromtimestamp(int(date)/1000)
    a_week_ago = datetime.fromtimestamp((int(date) - 2592000000)/1000)
    month_food_posts = FoodPost.objects.filter(author=self.request.user, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    month_food_data = FoodConsumption.objects.none() # 빈 쿼리셋
    for i in range(len(month_food_posts)):
      month_food_data |= month_food_posts[i].foodconsumption_set.all()
    # print(week_food_data)
    # week_supplement_data = SupplementPost.objects.filter(author=self.request.user, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    # TODO : supplement 데이터 쿼리셋 만들어서 보내기
    month_supplement_posts = SupplementPost.objects.filter(author=self.request.user, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    month_supplement_data = SupplementConsumption.objects.none() # 빈 쿼리셋 생성
    for i in range(len(month_supplement_posts)):
      month_supplement_data |= month_supplement_posts[i].supplementconsumption_set.all()
    # log
    # print(month_supplement_data)

    month_water_data = WaterPost.objects.filter(author=self.request.user, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    # print(week_food_data)
    # 기록 날짜 체크(today_date, author)
    # decreasing_date = today_date
    reporting_date = count_reporting_date(today_date, request.user, "month")
    sum_month_data = nutrient_calculator(month_food_data, month_supplement_data, month_water_data, reporting_date)
    # print(sum_month_data)
    return Response(data=sum_month_data)

# ADMIN : 관리자 페이지(사용자명을 입력하면 모든 정보 출력)
class AdminView(APIView):

  def get(self, request):
    author = request.GET.get('author', None)
    if author is None:
      user_list = User.objects.filter(is_superuser=False, is_staff=False)
      data = {
        'userList' : user_list
      }
      serializer = UserListSerializer(instance=data)
      return Response(data=serializer.data)
    else:
      # DEPRECATED
      user = User.objects.get(username=author)
      admin_data = {}
      sample_data = {'breakfast' : {'image' : [], 'data' : []}, 'lunch' : {'image' : [], 'data' : []} , 'dinner' : {'image' : [], 'data' : []} , 'snack' : {'image' : [], 'data' : []}, 'supplement' : [], 'water' : 0 }
      
      #=============================== BREAKFAST =======================================================
      breakfast_consumption = FoodConsumption.objects.filter(post__type="breakfast", post__author=user)
      breakfast_serializer = FoodAdminConsumptionSerializer(instance=breakfast_consumption, many=True) # join시 특정 필드만 가져오는 메서드?
      for elem in breakfast_serializer.data:
        formatted_elem = dict(elem)
        formatted_date = str(elem['date']).split(' ')[0]
        
        # 새로운 날짜면 템플릿 데이터(sample_data) 생성
        if formatted_date not in admin_data.keys():
          admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
          # admin_data[formatted_date] = copy.deepcopy(sample_data)
        admin_data[f"{formatted_date}"]['breakfast']['data'].append(formatted_elem)
        # admin_data[formatted_date]['breakfast']['data'].append(formatted_elem)

      breakfast_image = FoodImage.objects.filter(post__type="breakfast", post__author=user)
      breakfast_image_serializer = FoodAdminImageSerializer(instance=breakfast_image, many=True)
      for elem in breakfast_image_serializer.data:
        formatted_elem = dict(elem)
        # print(elem['date'])
        formatted_date = str(elem['date']).split(' ')[0]
        # 새로운 날짜면 템플릿 데이터 생성
        if formatted_date not in admin_data.keys():
          admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
        admin_data[f"{formatted_date}"]['breakfast']['image'].append(formatted_elem)

      #=============================== LUNCH =======================================================
      lunch_consumption = FoodConsumption.objects.filter(post__type="lunch", post__author=user)
      lunch_serializer = FoodAdminConsumptionSerializer(instance=lunch_consumption, many=True) # join시 특정 필드만 가져오는 메서드?
      for elem in lunch_serializer.data:
        formatted_elem = dict(elem)
        formatted_date = str(elem['date']).split(' ')[0]
        
        # 새로운 날짜면 템플릿 데이터(sample_data) 생성
        if formatted_date not in admin_data.keys():
          admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
        admin_data[f"{formatted_date}"]['lunch']['data'].append(formatted_elem)

      lunch_image = FoodImage.objects.filter(post__type="lunch", post__author=user)
      lunch_image_serializer = FoodAdminImageSerializer(instance=lunch_image, many=True)
      for elem in lunch_image_serializer.data:
        formatted_elem = dict(elem)
        formatted_date = str(elem['date']).split(' ')[0]
        # 새로운 날짜면 템플릿 데이터 생성
        if formatted_date not in admin_data.keys():
          admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
        admin_data[f"{formatted_date}"]['lunch']['image'].append(formatted_elem)

      #=============================== DINNER =======================================================zz
      dinner_consumption = FoodConsumption.objects.filter(post__type="dinner", post__author=user)
      dinner_serializer = FoodAdminConsumptionSerializer(instance=dinner_consumption, many=True) # join시 특정 필드만 가져오는 메서드?
      for elem in dinner_serializer.data:
        formatted_elem = dict(elem)
        formatted_date = str(elem['date']).split(' ')[0]
        
        # 새로운 날짜면 템플릿 데이터(sample_data) 생성
        if formatted_date not in admin_data.keys():
          admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
        admin_data[f"{formatted_date}"]['dinner']['data'].append(formatted_elem)

      dinner_image = FoodImage.objects.filter(post__type="dinner", post__author=user)
      dinner_image_serializer = FoodAdminImageSerializer(instance=dinner_image, many=True)
      for elem in dinner_image_serializer.data:
        formatted_elem = dict(elem)
        formatted_date = str(elem['date']).split(' ')[0]
        # 새로운 날짜면 템플릿 데이터 생성
        if formatted_date not in admin_data.keys():
          admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
        admin_data[f"{formatted_date}"]['dinner']['image'].append(formatted_elem)

      #=============================== SNACK =========================================================
      snack_consumption = FoodConsumption.objects.filter(post__type="snack", post__author=user)
      snack_serializer = FoodAdminConsumptionSerializer(instance=snack_consumption, many=True) # join시 특정 필드만 가져오는 메서드?
      for elem in snack_serializer.data:
        formatted_elem = dict(elem)
        formatted_date = str(elem['date']).split(' ')[0]
        
        # 새로운 날짜면 템플릿 데이터(sample_data) 생성
        if formatted_date not in admin_data.keys():
          admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
        admin_data[f"{formatted_date}"]['snack']['data'].append(formatted_elem)

      snack_image = FoodImage.objects.filter(post__type="snack", post__author=user)
      snack_image_serializer = FoodAdminImageSerializer(instance=snack_image, many=True)
      for elem in snack_image_serializer.data:
        formatted_elem = dict(elem)
        formatted_date = str(elem['date']).split(' ')[0]
        # 새로운 날짜면 템플릿 데이터 생성
        if formatted_date not in admin_data.keys():
          admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
        admin_data[f"{formatted_date}"]['snack']['image'].append(formatted_elem)

      #=========================== *SUPPLEMENT* =========================================================
      # supplement_consumption = SupplementPost.objects.filter(author=user)
      # supplement_serializer = SupplementSerializer(instance=supplement_consumption, many=True)
      supplement_consumption = SupplementConsumption.objects.filter(post__author=user)
      supplement_serializer = SupplementConsumptionSerializer(instance=supplement_consumption, many=True)
      for elem in supplement_serializer.data:
        # print(elem)
        post_created = SupplementPost.objects.get(id=elem['post']).created_at
        # print(post_created)
        # print(str(post_created).split(' ')[0])
        formatted_elem = dict(elem)
        # formatted_date = str(elem['created_at']).split('T')[0] # 얘는 왜 T? => serializer 차이?
        formatted_date = str(post_created).split(' ')[0]
        # 새로운 날짜면 템플릿 데이터 생성
        if formatted_date not in admin_data.keys():
          admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
        admin_data[f"{formatted_date}"]['supplement'].append(formatted_elem)

      #=========================== WATER =========================================================
      water_consumption = WaterPost.objects.filter(author=user)
      water_serializer = WaterSerializer(instance=water_consumption, many=True)
      for elem in water_serializer.data:
        formatted_date = str(elem['created_at']).split('T')[0]
        # 새로운 날짜면 템플릿 데이터 생성
        if formatted_date not in admin_data.keys():
          admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
        admin_data[f"{formatted_date}"]['water'] = elem['amount']

      # 날짜 오름차순 정렬
      admin_data = dict(sorted(admin_data.items()))
      return Response(data=admin_data)

# ADMIN VIEW를 DAY/WEEK/MONTH로 나눠서 보여주기
class AdminSumView(APIView):
  
  def get(self, request):
    author_string = self.request.GET.get('author', None)
    author = User.objects.get(username=author_string)
    date = self.request.GET.get('date', None)
    sum_type = self.request.GET.get('type', None)
    if sum_type == 'day':
      start_date = datetime.fromtimestamp(int(date)/1000)
    elif sum_type == 'week':
      start_date = datetime.fromtimestamp((int(date) - 518400000)/1000)
    elif sum_type == 'month':
      start_date = datetime.fromtimestamp((int(date) - 2592000000)/1000)
    
    today_date = datetime.fromtimestamp(int(date)/1000)

    user = User.objects.get(username=author)
    admin_data = {}
    sample_data = {'breakfast' : {'image' : [], 'data' : []}, 'lunch' : {'image' : [], 'data' : []} , 'dinner' : {'image' : [], 'data' : []} , 'snack' : {'image' : [], 'data' : []}, 'supplement' : [], 'water' : 0 }

    breakfast_consumption = FoodConsumption.objects.filter(post__type="breakfast", post__author=user, post__created_at__lte=today_date, post__created_at__gte=start_date)
    breakfast_serializer = FoodAdminConsumptionSerializer(instance=breakfast_consumption, many=True) # join시 특정 필드만 가져오는 메서드?
    for elem in breakfast_serializer.data:
      formatted_elem = dict(elem)
      formatted_date = str(elem['date']).split(' ')[0]

      # 새로운 날짜면 템플릿 데이터(sample_data) 생성
      if formatted_date not in admin_data.keys():
        admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
        # admin_data[formatted_date] = copy.deepcopy(sample_data)
      admin_data[f"{formatted_date}"]['breakfast']['data'].append(formatted_elem)
      # admin_data[formatted_date]['breakfast']['data'].append(formatted_elem)

    breakfast_image = FoodImage.objects.filter(post__type="breakfast", post__author=user, post__created_at__lte=today_date, post__created_at__gte=start_date)
    breakfast_image_serializer = FoodAdminImageSerializer(instance=breakfast_image, many=True)
    for elem in breakfast_image_serializer.data:
      formatted_elem = dict(elem)
      # print(elem['date'])
      formatted_date = str(elem['date']).split(' ')[0]
      # 새로운 날짜면 템플릿 데이터 생성
      if formatted_date not in admin_data.keys():
        admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
      admin_data[f"{formatted_date}"]['breakfast']['image'].append(formatted_elem)

    #=============================== LUNCH =======================================================
    lunch_consumption = FoodConsumption.objects.filter(post__type="lunch", post__author=user, post__created_at__lte=today_date, post__created_at__gte=start_date)
    lunch_serializer = FoodAdminConsumptionSerializer(instance=lunch_consumption, many=True) # join시 특정 필드만 가져오는 메서드?
    for elem in lunch_serializer.data:
      formatted_elem = dict(elem)
      formatted_date = str(elem['date']).split(' ')[0]
      
      # 새로운 날짜면 템플릿 데이터(sample_data) 생성
      if formatted_date not in admin_data.keys():
        admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
      admin_data[f"{formatted_date}"]['lunch']['data'].append(formatted_elem)

    lunch_image = FoodImage.objects.filter(post__type="lunch", post__author=user, post__created_at__lte=today_date, post__created_at__gte=start_date)
    lunch_image_serializer = FoodAdminImageSerializer(instance=lunch_image, many=True)
    for elem in lunch_image_serializer.data:
      formatted_elem = dict(elem)
      formatted_date = str(elem['date']).split(' ')[0]
      # 새로운 날짜면 템플릿 데이터 생성
      if formatted_date not in admin_data.keys():
        admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
      admin_data[f"{formatted_date}"]['lunch']['image'].append(formatted_elem)

    #=============================== DINNER =======================================================zz
    dinner_consumption = FoodConsumption.objects.filter(post__type="dinner", post__author=user, post__created_at__lte=today_date, post__created_at__gte=start_date)
    dinner_serializer = FoodAdminConsumptionSerializer(instance=dinner_consumption, many=True) # join시 특정 필드만 가져오는 메서드?
    for elem in dinner_serializer.data:
      formatted_elem = dict(elem)
      formatted_date = str(elem['date']).split(' ')[0]
      
      # 새로운 날짜면 템플릿 데이터(sample_data) 생성
      if formatted_date not in admin_data.keys():
        admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
      admin_data[f"{formatted_date}"]['dinner']['data'].append(formatted_elem)

    dinner_image = FoodImage.objects.filter(post__type="dinner", post__author=user, post__created_at__lte=today_date, post__created_at__gte=start_date)
    dinner_image_serializer = FoodAdminImageSerializer(instance=dinner_image, many=True)
    for elem in dinner_image_serializer.data:
      formatted_elem = dict(elem)
      formatted_date = str(elem['date']).split(' ')[0]
      # 새로운 날짜면 템플릿 데이터 생성
      if formatted_date not in admin_data.keys():
        admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
      admin_data[f"{formatted_date}"]['dinner']['image'].append(formatted_elem)

    #=============================== SNACK =========================================================
    snack_consumption = FoodConsumption.objects.filter(post__type="snack", post__author=user, post__created_at__lte=today_date, post__created_at__gte=start_date)
    snack_serializer = FoodAdminConsumptionSerializer(instance=snack_consumption, many=True) # join시 특정 필드만 가져오는 메서드?
    for elem in snack_serializer.data:
      formatted_elem = dict(elem)
      formatted_date = str(elem['date']).split(' ')[0]
      
      # 새로운 날짜면 템플릿 데이터(sample_data) 생성
      if formatted_date not in admin_data.keys():
        admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
      admin_data[f"{formatted_date}"]['snack']['data'].append(formatted_elem)

    snack_image = FoodImage.objects.filter(post__type="snack", post__author=user, post__created_at__lte=today_date, post__created_at__gte=start_date)
    snack_image_serializer = FoodAdminImageSerializer(instance=snack_image, many=True)
    for elem in snack_image_serializer.data:
      formatted_elem = dict(elem)
      formatted_date = str(elem['date']).split(' ')[0]
      # 새로운 날짜면 템플릿 데이터 생성
      if formatted_date not in admin_data.keys():
        admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
      admin_data[f"{formatted_date}"]['snack']['image'].append(formatted_elem)

    #=========================== *SUPPLEMENT* =========================================================
    # supplement_consumption = SupplementPost.objects.filter(author=user)
    # supplement_serializer = SupplementSerializer(instance=supplement_consumption, many=True)
    supplement_consumption = SupplementConsumption.objects.filter(post__author=user, post__created_at__lte=today_date, post__created_at__gte=start_date)
    supplement_serializer = SupplementConsumptionSerializer(instance=supplement_consumption, many=True)
    for elem in supplement_serializer.data:
      # print(elem)
      post_created = SupplementPost.objects.get(id=elem['post']).created_at
      # print(post_created)
      # print(str(post_created).split(' ')[0])
      formatted_elem = dict(elem)
      # formatted_date = str(elem['created_at']).split('T')[0] # 얘는 왜 T? => serializer 차이?
      formatted_date = str(post_created).split(' ')[0]
      # 새로운 날짜면 템플릿 데이터 생성
      if formatted_date not in admin_data.keys():
        admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
      admin_data[f"{formatted_date}"]['supplement'].append(formatted_elem)

    #=========================== WATER =========================================================
    water_consumption = WaterPost.objects.filter(author=user, created_at__lte=today_date, created_at__gte=start_date)
    water_serializer = WaterSerializer(instance=water_consumption, many=True)
    for elem in water_serializer.data:
      formatted_date = str(elem['created_at']).split('T')[0]
      # 새로운 날짜면 템플릿 데이터 생성
      if formatted_date not in admin_data.keys():
        admin_data[f"{formatted_date}"] = copy.deepcopy(sample_data)
      admin_data[f"{formatted_date}"]['water'] = elem['amount']

    # 날짜 오름차순 정렬
    admin_data = dict(sorted(admin_data.items()))
    return Response(data=admin_data)

# ADMIN DAY/WEEK/MONTH : 관리자 식이분석 페이지(사용자명과 날짜를 입력하면 일별/주별/월별 식이분석 결과 출력)
class AdminDayView(APIView):

  def get(self, request):
    author_string = self.request.GET.get('author', None)
    if author_string is None:
      author = self.request.user
    else:
      author = User.objects.get(username=author_string)
    # if author_string is None:
    #   data = {
    #     'error_msg' : '올바른 사용자 코드를 입력하세요.'
    #   }
    #   return Response(status=status.HTTP_404_NOT_FOUND, data=data)
    # author = User.objects.get(username=author_string)

    date = self.request.GET.get('date', None)
    int_date = convert_to_int_date(date)
    if int_date is None:
      data = {
        'error_msg' : '올바른 날짜를 입력하세요.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)

    date = datetime.fromtimestamp(int_date/1000)
    nutrient = self.request.GET.get('nutrient', None) # nutrient 포함 여부
    # 아침/점심/저녁/간식 영양소
    #food_posts = list(FoodPost.objects.filter(author=author, created_at=date).values('id')) # 기존
    # 변경 - Queryset으로 받아오기 ***
    food_posts = FoodPost.objects.filter(author=author, created_at=date)
    day_food_data = FoodConsumption.objects.none() # 빈 쿼리셋 생성
    if nutrient == 'yes':
      for i in range(len(food_posts)):
        #day_food_data |= FoodConsumption.objects.filter(post=food_posts[i]['id']) # 기존
        day_food_data |= food_posts[i].foodconsumption_set.all()
    else: # nutrient == 'no'
      for i in range(len(food_posts)):
        day_food_data |= food_posts[i].foodconsumption_set.exclude(food__category="보충제")
    # 물 정보 가져오기
    day_water_data = WaterPost.objects.filter(author=author, created_at=date)
    reporting_date = count_reporting_date(date, author, "day")
    # supplement 테이블 사용 X(deprecated) - 임시
    day_supplement_data = SupplementConsumption.objects.none() 
    sum_day_data = nutrient_calculator(day_food_data, day_supplement_data, day_water_data, reporting_date)
    return Response(data=sum_day_data)

class AdminWeekView(APIView):

  def get(self, request):
    author_string = self.request.GET.get('author', None)
    if author_string is None:
      author = self.request.user
    else:
      author = User.objects.get(username=author_string)
    date = self.request.GET.get('date', None)
    nutrient = self.request.GET.get('nutrient', None) # nutrient 포함 여부
    today_date = datetime.fromtimestamp(int(date)/1000)
    a_week_ago = datetime.fromtimestamp((int(date) - 518400000)/1000)
    week_food_posts = FoodPost.objects.filter(author=author, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    week_food_data = FoodConsumption.objects.none() # 빈 쿼리셋
    if nutrient == 'yes':
      for i in range(len(week_food_posts)):
        week_food_data |= week_food_posts[i].foodconsumption_set.all()
    else: # nutrient == 'no'
      for i in range(len(week_food_posts)):
        week_food_data |= week_food_posts[i].foodconsumption_set.exclude(food__category="보충제")
    
    week_water_data = WaterPost.objects.filter(author=author, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    reporting_date = count_reporting_date(today_date, author, "week")
    # supplement 테이블 사용 X(deprecated) - 임시
    week_supplement_data = SupplementConsumption.objects.none() 
    sum_week_data = nutrient_calculator(week_food_data, week_supplement_data, week_water_data, reporting_date)

    return Response(data=sum_week_data)

class AdminMonthView(APIView):

  def get(self, request):
    author_string = self.request.GET.get('author', None)
    if author_string is None:
      author = self.request.user
    else:
      author = User.objects.get(username=author_string)
    date = self.request.GET.get('date', None)
    nutrient = self.request.GET.get('nutrient', None) # nutrient 포함 여부
    today_date = datetime.fromtimestamp(int(date)/1000)
    a_week_ago = datetime.fromtimestamp((int(date) - 2592000000)/1000)
    month_food_posts = FoodPost.objects.filter(author=author, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    month_food_data = FoodConsumption.objects.none() # 빈 쿼리셋
    if nutrient == 'yes':
      for i in range(len(month_food_posts)):
        month_food_data |= month_food_posts[i].foodconsumption_set.all()
    else: # nutrient == 'no':
      for i in range(len(month_food_posts)):
        month_food_data |= month_food_posts[i].foodconsumption_set.exclude(food__category="보충제")
        
    month_water_data = WaterPost.objects.filter(author=author, created_at__lte=today_date, created_at__gte=a_week_ago).order_by('created_at')
    reporting_date = count_reporting_date(today_date, author, "month")
    # supplement 테이블 사용 X(deprecated) - 임시
    month_supplement_data = SupplementConsumption.objects.none() 
    sum_month_data = nutrient_calculator(month_food_data, month_supplement_data, month_water_data, reporting_date)

    return Response(data=sum_month_data)

# admin - 사용자별 식단 수정(기존api)/삭제(기존api)/입력(새로운 api)
# POST만 구현 (image는 모두 무시**)
class AdminPostCreateView(CreateAPIView):
  queryset = FoodPost.objects.all()
  serializer_class = FoodPostSerializer

  def create(self, request, *args, **kwargs):
        # 예외처리 : 이상한 값 입력 시 예외처리
        try:
          image_list = [] # image 무시 **
          consumption_list = request.data['consumptions']
          meal_type = request.data['type']
          created_at = request.data['created_at']
          author = request.data['author'] # 작성자(target)
        except KeyError:
          data = {
            'err_msg' : "입력한 JSON이 올바른 형태인지 확인해주세요 (fields: consumptions, type, created_at(unix time))"
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        # 예외처리 : Food 입력 시 consumptions는 반드시 있어야 함(image는 모두 무시**)
        if consumption_list == []:
          data = {
            "err_msg" : "음식 정보나 음식 이미지 둘 중 하나는 반드시 입력해야 합니다!" 
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        # 예외처리
        if meal_type not in MEAL_TYPE_LIST:
          data = {
            "err_msg" : "type은 반드시 breakfast, lunch, dinner, snack 중 하나여야 합니다!" 
          }
          return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

        date_data = datetime.fromtimestamp(int(created_at)/1000)

        # 입력받은 author 처리 필요
        author_id = User.objects.get(username=author).id

        data = {
          "type" : meal_type,
          "created_at" : date_data,
          "author" : author_id, # FK
          "images" : image_list, # []
          "consumptions": consumption_list,
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # print(f"최종 SERIALZIER.DATA : {serializer.data}") # 
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)