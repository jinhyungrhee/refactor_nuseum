from django.shortcuts import render
from .models import Post
from .serializers import PostSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from consumptions.serializers import ConsumptionSerializer, WaterSerializer, ImageDecodeSerializer
from consumptions.models import Consumption, WaterConsumption
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from datetime import datetime
import json

# Date를 이용하여 Post에 접근하는 뷰 -> GET, POST 메서드
class PostDateView(APIView):

  # parser_classes = (MultiPartParser, FormParser) # 에러 나면 테스트

  # 날짜로 해당 post 가져오는 메서드
  def get_post(self, request, date):
    try:
      post = Post.objects.get(author=self.request.user, created_at=date)
      return post
    except Post.DoesNotExist:
      return None
    except Post.MultipleObjectsReturned:
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
      breakfast_consumptions = Consumption.objects.filter(post=post.id, meal_type='breakfast')
      lunch_consumptions = Consumption.objects.filter(post=post.id, meal_type='lunch')
      dinner_consumptions = Consumption.objects.filter(post=post.id, meal_type='dinner')
      snack_consumptions = Consumption.objects.filter(post=post.id, meal_type='snack')
      water_consumption = WaterConsumption.objects.get(post=post.id)
      # 데이터 가져오는 쿼리문 추가
      print(water_consumption.amount)
       # Queryset to JSON
      # data = consumptions.values()
      data = {
        'meal' : {
          'breakfast' : {
            'data' : breakfast_consumptions.values(),
            'image' : '',
          },
          'lunch' : {
            'data' : lunch_consumptions.values(),
            'image' : '',
          },
          'dinner' : {
            'data' : dinner_consumptions.values(),
            'image' : '',
          },
          'snack' : {
            'data' : snack_consumptions.values(),
            'image' : '',
          }
        },
        'water' : water_consumption.amount,
        'post_id': post.id,
      }
      return Response(data=data) 
    else:
      data = {
        'error_msg' : '해당 날짜에 작성된 포스트가 존재하지 않거나 두 개 이상입니다.(두 개 이상인 경우는 테스트에서만 발생)'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)

  def post(self, request):
    print("============================================== LOG ====================================")
    print(request.data)
    print(request.POST)
    print(request.FILES)
    print("========================================================================================")
    # 아무 값도 입력하지 않았을 때 예외처리(400 에러 리턴)
    if request.data['meal'] == {}:
      data = {
        'empty_value_error' : '최소 한 끼는 반드시 입력해야 합니다.'
      }
      return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

    # 날짜 변환: unix timestamp string(1660575600000) -> datetime
    request.data['created_at'] = datetime.fromtimestamp(int(request.data['created_at'])/1000)
    
    # 1. postSerializer 통해 역직렬화하여 값을 DB에 저장 -> Post 객체 생성
    serializer = PostSerializer(data=request.data)
    # print(serializer)
    if serializer.is_valid():
      post = serializer.save(
        author=request.user
      )
      post_serializer = PostSerializer(post).data # 포스트 생성**
      
      # 2. 포스트가 생성되고 난 뒤에 그 다음에 해당 post id를 가지고 Post_Consumption 테이블 지정
      # 2-1. 입력받은 데이터로 음식 consumption 생성하는 로직**
      # 방금 생성된 포스트의 pk값 가져오기 -> 전체적으로 사용됨! ** <<post_id는 전역변수처럼 사용>>
      post_id = post_serializer['id']
      
      # 수정중====================================================================================
      # for elem in request.data['meal']: # meal -> food 변경 예정
      #   # 입력받은 값들을 consumption 객체의 각 필드에 입력
      #   food_id = elem['food_id']
      #   food_amount = elem['amount']
      #   meal_type = elem['meal_type']
      #   # img1 = elem[3] # 다른 타입으로 들어옴
      #   # print(elem[3])
      #   # img2 = elem[4]
      #   # img3 = elem[5]
      #   # TODO : 이미지를 올리고 이미지의 url을 저장

      #   consumption_data = {
      #     'post' : post_id,
      #     'food' : food_id,
      #     'amount' : food_amount,
      #     'meal_type' : meal_type,
      #     # 'img1' : img1,
      #     # 'img2' : img2,
      #     # 'img3' : img3,
      #   }

      #   consumption_serializer = ConsumptionSerializer(data=consumption_data)
      #   if consumption_serializer.is_valid():
      #     # consumption 객체 생성
      #     consumption_serializer.save()
      #   else:
      #     return Response(status=status.HTTP_400_BAD_REQUEST, data=consumption_serializer.errors)
      
      # ===================================== 수정중 ====================================================
      # <1> request.data['meal'] 부분 처리
      # <1>-1 'meal'(foods)의 'data' 입력값들부터 처리
      for i in range(4):
        classifier = ['breakfast', 'lunch', 'dinner', 'snack'] # 처음에 meal_type이 결정되므로 따로 받지 않아도 될듯? **
        for elem in request.data['meal'][classifier[i]]: # meal -> food 변경 예정
          # print(request.data['meal'][classifier[i]]) # dict
          temp_dict = request.data['meal'][classifier[i]] 
          # *temp_dict*
          # {'data': [{'food_id': 4, 'amount': 400}, {'food_id': 3, 'amount': 300}, {'food_id': 2, 'amount': 200}, {'food_id': 1, 'amount': 100}], 
          #  'image': []}
          print(temp_dict)
          if elem == 'data':
            # print(temp_dict['data'])
            for elem in temp_dict['data']:
              # 입력받은 값들을 consumption 객체의 각 필드에 입력
              food_id = elem['food_id']
              food_amount = elem['amount']

              consumption_data = {
                'post' : post_id,
                'food' : food_id, # *
                'amount' : food_amount, # *
                'meal_type' : classifier[i],
              }

              consumption_serializer = ConsumptionSerializer(data=consumption_data)
              if consumption_serializer.is_valid():
                # consumption 객체 생성
                consumption_serializer.save()
              else:
                return Response(status=status.HTTP_400_BAD_REQUEST, data=consumption_serializer.errors)
          # <1>-2. 'img'부분 처리
          else: # elem(str) == 'img'
            for elem in temp_dict['image']: # image 개수만큼 for문을 돌기 때문에, 굳이 음식 개수와 이미지 개수를 맞출 필요는 없음!
              image = temp_dict['image']
              # print(image)
              image_data = {
                'post' : post_id,
                'image' : image,
                'meal_type' : classifier[i],
              }
              # print(image_data)
              # 입력 값이 맞는지 체크 필요!
              image_decode_serializer = ImageDecodeSerializer(data=image_data, context={'request':request, 'images':data.get('images')})
              if image_decode_serializer.is_valid():
                image_decode_serializer.save()
                return Response(data=image_decode_serializer.data, status=status.HTTP_201_CREATED)
              return Response(data=image_decode_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


      # 2-2. 입력받은 데이터로 '수분(물)' consumption 생성하는 로직** (수분은 '단일 값'만 입력받음)
      post_id = post_serializer['id']
      # print(request.data['water'])
      water_amount = request.data['water']
      
      water_consumption_data = {
        'post' : post_id,
        'amount' : water_amount,
      }

      water_serializer = WaterSerializer(data=water_consumption_data)
      # print(water_serializer)
      if water_serializer.is_valid():
        water_serializer.save()
      else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=water_serializer.errors)

      return Response(data=post_serializer, status=status.HTTP_200_OK)
    else:
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ID(PK)를 이용하여 Post에 접근하는 뷰 -> GET, PUT 메서드 처리
class PostIdView(APIView):

  # pk로 해당 post 가져오는 메서드
  def get_post_by_id(self, pk):
    try:
      post = Post.objects.get(pk=pk)
      return post
    except Post.DoesNotExist:
      return None

  def get(self, request, pk):

    post = self.get_post_by_id(pk)
    if post is not None:
      
      # 예외처리
      if post.author != request.user:
        data = {
          'error_msg' : '포스트의 작성자가 아닙니다.'
        }
        return Response(status=status.HTTP_403_FORBIDDEN, data=data)

      breakfast_consumptions = Consumption.objects.filter(post=post.id, meal_type='breakfast')
      lunch_consumptions = Consumption.objects.filter(post=post.id, meal_type='lunch')
      dinner_consumptions = Consumption.objects.filter(post=post.id, meal_type='dinner')
      snack_consumptions = Consumption.objects.filter(post=post.id, meal_type='snack')
      water_consumption = WaterConsumption.objects.get(post=post.id)
       # Queryset to JSON
      # data = consumptions.values()
      # =======================* 경준님이 원하는 출력 형식 *(참고)===================================
      data = {
        'foods' : {
          'breakfast' : {
            'data' : breakfast_consumptions.values(),
            # 'image' : breakfast_consumptions.image,
            'image' : [],
          },
          'lunch' : {
            'data' : lunch_consumptions.values(),
            # 'image' : lunch_consumptions.image,
            'image' : [],
          },
          'dinner' : {
            'data' : dinner_consumptions.values(),
            # 'image' : dinner_consumptions.image,
            'image' : [],
          },
          'snack' : {
            'data' : snack_consumptions.values(),
            # 'image' : snack_consumptions.image,
            'image' : [],
          }
        },
        'water_amount' : water_consumption.amount,
        'post_id' : post.id,
      }
      return Response(data=data)

    else:
      data = {
        'error_msg' : '작성된 포스트가 존재하지 않습니다.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)

  # PUT은 좀 나중에 수정...ㅠㅠ
  # 순서 쌍 or 특정 개체에 대한 수정 => PUT 메서드 수정 필요! ****** (id_get 메서드를 수정하는 로직에만 사용?)
  def put(self, request, pk):
    
    post = self.get_post_by_id(pk)
    if post is not None:
      if post.author != request.user:
        data = {
          'error_msg' : '포스트의 작성자가 아닙니다.'
        }
        return Response(status=status.HTTP_403_FORBIDDEN, data=data)

      # <1> 음식에 대해서 PUT 처리**
      consumptions = Consumption.objects.filter(post=post.id)
      # print(consumptions)
      # print(len(consumptions)) # target
      # print(len(request.data['meal'])) # input
      for i in range(len(request.data['meal'])):
        # print(consumptions[i])
        # 1-1.빈 리스트는 '삭제' 처리
        if request.data['meal'][i] == {}:
          food_data = {
            "deprecated" : True
          }
        else:
          # 1-2.빈 리스트가 아닌 것들은 '수정' 또는 '생성'
          food_data = {
            'post' : post.id,
            'food' : request.data['meal'][i]['food_id'],
            'amount' : request.data['meal'][i]['amount'],
            'meal_type' : request.data['meal'][i]['meal_type']
          }

        # 2-1.수정하려는 consumption의 수보다 request.data의 수가 작거나 같을 때에만 해당 쌍에 맞춰서 수정 진행
        if i < len(consumptions):
          consumption_update_serializer = ConsumptionSerializer(consumptions[i], data=food_data, partial=True)
          # print(request.data['meal'][i])
          if consumption_update_serializer.is_valid():
            # 각 consumption 객체 update
            consumption_update_serializer.save()
          else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=consumption_update_serializer.errors)
        # 2-2.수정하려는 consumption의 수보다 request.data의 수가 더 많으면 "추가로 생성"
        else: 
          consumption_create_serializer = ConsumptionSerializer(data=food_data)
          if consumption_create_serializer.is_valid():
            consumption_create_serializer.save()

      # <2> 수분(물)에 대해서 PUT 처리**
      water_consumption = WaterConsumption.objects.get(post=post.id)
      water_data = {
        'post' : post.id,
        'amount' : request.data['water']
      }
      water_update_serializer = WaterSerializer(water_consumption, data=water_data, partial=True)
      if water_update_serializer.is_valid():
        water_update_serializer.save()
      else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=water_update_serializer.errors)

      # for i in range(len(request.data['water'])):
      #   if request.data['water'][i] == -1: # water.amount 값으로 -1을 보내면 삭제 처리
      #     water_data = {
      #       "deprecated" : True
      #     }
      #   else:
      #     water_data = {
      #       'post' : post.id,
      #       'amount' : request.data['water'][i]
      #     }

      #   if i < len(water_consumptions): # update
      #     water_update_serializer = WaterSerializer(water_consumptions[i], data=water_data, partial=True)
      #     if water_update_serializer.is_valid():
      #       water_update_serializer.save()
      #     else:
      #       return Response(status=status.HTTP_400_BAD_REQUEST, data=water_update_serializer.errors)
      #   else: # 추가 생성
      #     water_create_serializer = WaterSerializer(data=water_data)
      #     if water_create_serializer.is_valid():
      #       water_create_serializer.save()

      # 수정 & 추가 생성이 완료되었으면 deprecated consumption는 삭제
      try:
        deprecated_food_consumptions = Consumption.objects.filter(post=post.id, deprecated=True)
        # deprecated_water_consumptons = WaterConsumption.objects.filter(post=post.id, deprecated=True)
        # print(deprecated_consumptions)
        deprecated_food_consumptions.delete()
        # deprecated_water_consumptons.delete()
        print('deprecated consumptions 삭제 완료!')
      except:
        print('deprecated consumptions가 존재하지 않습니다!')

      breakfast_consumptions = Consumption.objects.filter(post=post.id, meal_type='breakfast')
      lunch_consumptions = Consumption.objects.filter(post=post.id, meal_type='lunch')
      dinner_consumptions = Consumption.objects.filter(post=post.id, meal_type='dinner')
      snack_consumptions = Consumption.objects.filter(post=post.id, meal_type='snack')
      water_consumption = WaterConsumption.objects.get(post=post.id)
      data = {
        'meal' : {
          'breakfast' : {
            'foods' : breakfast_consumptions.values(),
            # 'image' : breakfast_consumptions.image,
          },
          'lunch' : {
            'foods' : lunch_consumptions.values(),
            # 'image' : lunch_consumptions.image,
          },
          'dinner' : {
            'foods' : dinner_consumptions.values(),
            # 'image' : lunch_consumptions.iamge,
          },
          'snack' : {
            'foods' : snack_consumptions.values(),
            # 'image' : snack_consumptions.image,
          }
        },
        'water' : water_consumption.amount,
        'post_id' : post.id,
      }
      return Response(data=data, status=status.HTTP_200_OK)
    else:
      data = {
        'error_msg' : '포스트가 존재하지 않습니다.'
      }
      return Response(status=status.HTTP_400_BAD_REQUEST, data=data)
