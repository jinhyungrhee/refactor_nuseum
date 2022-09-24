from django.shortcuts import render
from .models import Post
from .serializers import PostSerializer
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from consumptions.serializers import ConsumptionSerializer, WaterSerializer, ImageDecodeSerializer, SupplementSerializer, SupplementDetailSerializer
from consumptions.models import Consumption, WaterConsumption, FoodImage, SupplementConsmption
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from datetime import datetime
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
from datetime import datetime
import boto3
from consumptions.utils import create_image_url, delete_image

# Date를 이용하여 Post에 접근하는 뷰 -> GET, POST 메서드
class PostDateView(APIView):

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
      # breakfast 이미지 처리
      breakfast_images = FoodImage.objects.filter(post=post.id, meal_type='breakfast')
      # print(breakfast_images)
      # 쿼리셋에서 이미지 이름들을 꺼내서 경로로 변경해서 리스트로 저장하는 로직 추가(가능하면 함수로 뺄 것!) 
      breakfast_images_queryset = breakfast_images.values('image')
      breakfast_images_list = []
      for i in range(len(breakfast_images_queryset)):
        breakfast_images_list.append(breakfast_images_queryset[i]['image'])
      
      lunch_consumptions = Consumption.objects.filter(post=post.id, meal_type='lunch')
      # lunch 이미지 처리
      lunch_images = FoodImage.objects.filter(post=post.id, meal_type='lunch')
      lunch_images_queryset = lunch_images.values('image')
      lunch_images_list = []
      for i in range(len(lunch_images_queryset)):
        lunch_images_list.append(lunch_images_queryset[i]['image'])
      
      dinner_consumptions = Consumption.objects.filter(post=post.id, meal_type='dinner')
      # dinner 이미지 처리
      dinner_images = FoodImage.objects.filter(post=post.id, meal_type='dinner')
      dinner_images_queryset = dinner_images.values('image')
      dinner_images_list = []
      for i in range(len(dinner_images_queryset)):
        dinner_images_list.append(dinner_images_queryset[i]['image'])
      
      snack_consumptions = Consumption.objects.filter(post=post.id, meal_type='snack')
      # snack 이미지 처리
      snack_images = FoodImage.objects.filter(post=post.id, meal_type='snack')
      snack_images_queryset = snack_images.values('image')
      snack_images_list = []
      for i in range(len(snack_images_queryset)):
        snack_images_list.append(snack_images_queryset[i]['image'])

      water_consumption = WaterConsumption.objects.get(post=post.id)
      supplement_consumption = SupplementConsmption.objects.filter(post=post.id)
      supplements = SupplementDetailSerializer(instance=supplement_consumption, many=True) # 직렬화 (DB -> JSON)
      # Queryset to JSON
      data = {
        'meal' : {
          'breakfast' : {
            'data' : breakfast_consumptions.values(),
            'image' : breakfast_images_list,
          },
          'lunch' : {
            'data' : lunch_consumptions.values(),
            'image' : lunch_images_list,
          },
          'dinner' : {
            'data' : dinner_consumptions.values(),
            'image' : dinner_images_list,
          },
          'snack' : {
            'data' : snack_consumptions.values(),
            'image' : snack_images_list,
          }
        },
        'water' : water_consumption.amount,
        'supplement' : supplements.data,
        'post_id': post.id,
      }
      return Response(data=data) 
    else:
      data = {
        'error_msg' : '해당 날짜에 작성된 포스트가 존재하지 않거나 두 개 이상입니다.(두 개 이상인 경우는 테스트에서만 발생)'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)
  
  def post(self, request):
    # 아무 값도 입력하지 않았을 때 예외처리(400 에러 리턴)
    if request.data['meal'] == {}:
      data = {
        'empty_value_error' : '최소 한 끼는 반드시 입력해야 합니다.'
      }
      return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

    # 날짜 변환: unix timestamp string(1660575600000) -> datetime
    date_data = datetime.fromtimestamp(int(request.data['created_at'])/1000) # 이미지 만들 때 context_data로 넘겨줘야 함!
    request.data['created_at'] = datetime.fromtimestamp(int(request.data['created_at'])/1000)
    
    # [1]. postSerializer 통해 역직렬화하여 값을 DB에 저장 -> Post 객체 생성
    serializer = PostSerializer(data=request.data)
    if serializer.is_valid():
      post = serializer.save(
        author=request.user
      )
      post_serializer = PostSerializer(post).data # 포스트 생성**

      # [2]. 포스트가 생성되고 난 뒤에 그 다음에 해당 post id를 가지고 Post_Consumption 테이블 지정
      # [2]-1. 입력받은 데이터로 음식 consumption 생성하는 로직**
      # 방금 생성된 포스트의 pk값 가져오기 -> 전체적으로 사용됨! ** <<post_id는 전역변수처럼 사용>>
      post_id = post_serializer['id'] 
      # <1> request.data['meal'] 부분 처리
      # <1>-1 'meal'(foods)의 'data' 입력값들부터 처리
      for i in range(4):
        classifier = ['breakfast', 'lunch', 'dinner', 'snack'] # 처음에 meal_type이 결정되므로 따로 받지 않아도 될듯? **
        for elem in request.data['meal'][classifier[i]]:
          temp_dict = request.data['meal'][classifier[i]] 
          # *temp_dict*
          # {'data': [{'food_id': 4, 'amount': 400}, {'food_id': 3, 'amount': 300}, {'food_id': 2, 'amount': 200}, {'food_id': 1, 'amount': 100}], 
          #  'image': []}
          if elem == 'data':
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
          # <1>-2. 'img'부분 처리 : base64 인코딩/디코딩
          else: # elem(str) == 'img'
            num = 0
            for elem in temp_dict['image']: # image 개수만큼 for문을 돌기 때문에, 굳이 음식 개수와 이미지 개수를 맞출 필요는 없음!
              image = temp_dict['image'] # 리스트 (리스트 전체가 아니라 개별 string을 넣는 것이 훨씬 빠름!)
              
              image_data = {
                # 'post' : post_id,
                'images' : image[num],
                'meal_type' : classifier[i],
              }
              
              # 입력 값이 맞는지 체크 필요!
              image_decode_serializer = ImageDecodeSerializer(data=image_data, context={'request':request, 'images':image_data.get('images'), 'post':post, 'meal_type':classifier[i], 'date':date_data, 'num' : num})
              num += 1 # PUT에서 값이 중복되는지 체크 필요 ** (num을 아예 내부적으로 할당해도 될듯?)
              if image_decode_serializer.is_valid():
                image_decode_serializer.save()
                # return Response(data=image_decode_serializer.data, status=status.HTTP_201_CREATED)
              else:
                return Response(data=image_decode_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


      # <2> 입력받은 데이터로 '수분(물)' consumption 생성하는 로직** (수분은 '단일 값'만 입력받음)
      water_amount = request.data['water']
      water_consumption_data = {
        'post' : post_id,
        'amount' : water_amount,
      }
      water_serializer = WaterSerializer(data=water_consumption_data)
      if water_serializer.is_valid():
        water_serializer.save()
      else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data=water_serializer.errors)

      # <3> 입력받은 데이터로 '영양제' consumption 생성하는 로직 (여러 개 입력 가능)
      supplement_input = request.data['supplement'] # supplement_data는 '리스트'일 것!
      supplement_count = len(supplement_input)
      for i in range(supplement_count):
        supplement_image = supplement_input[i]['image']
        supplement_name = supplement_input[i]['name']

        image_url = create_image_url(supplement_image, post_id, date_data, i) # s3에 객체 생성 후 url 리턴
        
        supplement_data = {
          'post' : post_id,
          'name' : supplement_name,
          'manufacturer' : supplement_input[i]['manufacturer'],
          # 'supplement_amount' : supplement_input[i]['amount'], # 일단 받지 않음.. 추후에 필요하면 추가!
          'image' : image_url,
        }
        supplement_serializer = SupplementSerializer(data=supplement_data)
        if supplement_serializer.is_valid():
          supplement_serializer.save()
        else:
          return Response(status=status.HTTP_400_BAD_REQUEST, data=supplement_serializer.errors)

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
      breakfast_images = FoodImage.objects.filter(post=post.id, meal_type='breakfast')
      breakfast_images_values = list(breakfast_images.values())
      breakfast_images_queryset = breakfast_images.values('image')
      breakfast_images_list = []
      for i in range(len(breakfast_images_queryset)):
        breakfast_images_list.append(breakfast_images_queryset[i]['image'])

      lunch_consumptions = Consumption.objects.filter(post=post.id, meal_type='lunch')
      lunch_images = FoodImage.objects.filter(post=post.id, meal_type='lunch')
      lunch_images_list = list(lunch_images.values())

      dinner_consumptions = Consumption.objects.filter(post=post.id, meal_type='dinner')
      dinner_images = FoodImage.objects.filter(post=post.id, meal_type='dinner')
      dinner_images_list = list(dinner_images.values())

      snack_consumptions = Consumption.objects.filter(post=post.id, meal_type='snack')
      snack_images = FoodImage.objects.filter(post=post.id, meal_type='snack')
      snack_images_list = list(snack_images.values())

      water_consumption = WaterConsumption.objects.get(post=post.id)
      supplement_consumption = SupplementConsmption.objects.filter(post=post.id)
      supplements = SupplementDetailSerializer(instance=supplement_consumption, many=True) # 직렬화 (DB -> JSON)
      # Queryset to JSON
      data = {
        'meal' : {
          'breakfast' : {
            'data' : breakfast_consumptions.values(),
            'image' : breakfast_images_list,
          },
          'lunch' : {
            'data' : lunch_consumptions.values(),
            'image' : lunch_images_list,
          },
          'dinner' : {
            'data' : dinner_consumptions.values(),
            'image' : dinner_images_list,
          },
          'snack' : {
            'data' : snack_consumptions.values(),
            'image' : snack_images_list,
          }
        },
        'water_amount' : water_consumption.amount,
        'supplement' : supplements.data,
        'post_id' : post.id,
      }
      return Response(data=data)

    else:
      data = {
        'error_msg' : '작성된 포스트가 존재하지 않습니다.'
      }
      return Response(status=status.HTTP_404_NOT_FOUND, data=data)

  # PUT 로직
  def put(self, request, pk):
    
    post = self.get_post_by_id(pk)
    date_data = post.created_at
    if post is not None:
      if post.author != request.user:
        data = {
          'error_msg' : '포스트의 작성자가 아닙니다.'
        }
        return Response(status=status.HTTP_403_FORBIDDEN, data=data)
      
      for i in range(4):
        classifier = ['breakfast', 'lunch', 'dinner', 'snack']
        for cateory in request.data['meal'][classifier[i]]: # 순서대로(=오름차순) 가져오는지 여부도 중요함!**
          consumptions = Consumption.objects.filter(post=post.id, meal_type=classifier[i])
          temp_dict = request.data['meal'][classifier[i]]
          len_data = len(temp_dict['data']) # 총 입력받은 음식 개체 수
          len_consumptions = len(consumptions) # 현재 해당 카테고리(ex. breakfast)에 존재하는 음식 개체 수
          if cateory == 'data':
            cnt_data = 0 # 현재 index
            for elem in temp_dict['data']:
              if cnt_data < len_consumptions: # 기존 개수에 포함되면 UPDATE
                if elem == {}:
                  food_data = {
                    "deprecated" : True
                  }
                else: # 업데이트 로직
                  food_data = {
                    'post' : post.id,
                    'food' : request.data['meal'][classifier[i]]['data'][cnt_data]['food_id'],
                    'amount' : request.data['meal'][classifier[i]]['data'][cnt_data]['amount'],
                    # meal_type은 고정임 -> 바꾸려면 다른 타입에 가서 생성해야 함!
                    # 'meal_type' : request.data['meal'][i]['meal_type'] # meal_type을 바꾸는건 여기서 지우고 다른곳에서 새로 생성하는 로직으로 구현
                  }
                # print(len_data, cnt_data)
                consumption_update_serializer = ConsumptionSerializer(consumptions[cnt_data], data=food_data, partial=True) # 여기까지 수정****
                if consumption_update_serializer.is_valid():
                  # 각 consumption 객체 update
                  consumption_update_serializer.save()
                else:
                  return Response(status=status.HTTP_400_BAD_REQUEST, data=consumption_update_serializer.errors)
              else: # 추가적인 개체들은 생성
                if elem != {}: # 추가했다가 바로 지우는 경우(=에러)는 제외
                  food_data = {
                    'post' : post.id,
                    'food' : request.data['meal'][classifier[i]]['data'][cnt_data]['food_id'],
                    'amount' : request.data['meal'][classifier[i]]['data'][cnt_data]['amount'],
                    'meal_type' : classifier[i]
                    # meal_type은 고정임 -> 바꾸려면 다른 타입에 가서 생성해야 함!
                    # 'meal_type' : request.data['meal'][i]['meal_type'] # meal_type을 바꾸는건 여기서 지우고 다른곳에서 새로 생성하는 로직으로 구현
                  }
                  # print("추가 음식 개체 생성!!!!")
                  consumption_create_serializer = ConsumptionSerializer(data=food_data)
                  if consumption_create_serializer.is_valid():
                    consumption_create_serializer.save()
                  else:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data=consumption_create_serializer.errors)
              cnt_data += 1  
          else: # category == 'image': => 'image' 갱신 로직 ================================= 여기까지 완료 =====================================
            image_instances = FoodImage.objects.filter(post=post.id, meal_type=classifier[i])
            # print("IMAGE:", image_instances)
            # print("IMAGE:", image_instances.values('image'))
            len_image = len(temp_dict['image'])
            len_food_images = len(image_instances)
            cnt_image = 0
            # print(temp_dict['image'])
            for elem in temp_dict['image']:
              if cnt_image < len_food_images:
                if elem == '':
                  # TODO : s3 삭제로직 추가 **
                  # S3에서 삭제
                  # print(food_images)
                  # print(image_instances.values('image')[cnt_image])
                  key = image_instances.values('image')[cnt_image]['image'].split('jinhyung.test.aws/')[1] # 파일명
                  # print(key)
                  s3_client = boto3.client(
                    's3',
                    aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                  )
                  s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
                  
                  # DB에서 삭제
                  image_data = {
                    'deprecated' : True
                  }
                  image_update_serializer = ImageDecodeSerializer(image_instances[cnt_image], data=image_data, partial=True) # 삭제 체크
                  if image_update_serializer.is_valid():
                    # 각 food_image 객체 삭제처리
                    image_update_serializer.save()
                    # print(image_update_serializer)
                  else:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data=image_update_serializer.errors)
              else: # 기존 이미지 이외로 들어온 것들에 대해서는 create 처리 (cnt_image >= len_image)
                if elem != "": # 추가했다가 바로 지우는 경우(=에러)는 제외
                  image_data = {
                    # 'post' : post_id,
                    'images' : temp_dict['image'][cnt_image], # 만약 PUT이 일어날 때는 IDX 처리를 어떻게 할 것인지 고민 필요! **
                    'meal_type' : classifier[i],
                  }
                  
                  # 입력 값이 맞는지 체크 필요! => ** 정상 동작! **
                  image_decode_serializer = ImageDecodeSerializer(data=image_data, context={'request':request, 'images':image_data.get('images'), 'post':post, 'meal_type':classifier[i], 'date':date_data, 'num' : cnt_image})
                  # num += 1 # PUT에서 값이 중복되는지 체크 필요 ** (num을 아예 내부적으로 할당해도 될듯?)
                  if image_decode_serializer.is_valid():
                    image_decode_serializer.save()
                    # return Response(data=image_decode_serializer.data, status=status.HTTP_201_CREATED)
                  else:
                    return Response(data=image_decode_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
              cnt_image += 1
      
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

      # <3> 영양제에 대해서 PUT 처리 - 수정하고 싶으면 기존에 존재하는 객체 삭제 후 재생성하는 방식!
      list_input_supplement = request.data['supplement']
      len_input_supplement = len(list_input_supplement)
      supplement_consumptions = SupplementConsmption.objects.filter(post=post.id)
      len_supplement_consupmtions = len(supplement_consumptions)
      # cnt_input_supplement = 0
      for i in range(len_input_supplement):
        if i < len_supplement_consupmtions:
          if list_input_supplement[i] == {}: # 삭제 마킹
            supplement_data = {
              'deprecated' : True
            }
            supplement_update_serializer = SupplementSerializer(supplement_consumptions[i], data=supplement_data, partial=True)
            if supplement_update_serializer.is_valid():
              supplement_update_serializer.save()
            else:
              return Response(status=status.HTTP_400_BAD_REQUEST, data=supplement_update_serializer.errors)
            # s3 이미지 삭제
            delete_image(supplement_consumptions[i].image)
        else: # 추가로 들어온 정보에 대해서는 create 수행
          # 추가했다가 바로 지우는 경우 예외처리(= {}객체가 생성되지만 해당 인덱스에 객체가 존재하지 않는 경우)
          if list_input_supplement[i] != {}:
            supplement_image = list_input_supplement[i]['image']
            supplement_name = list_input_supplement[i]['name']
            image_url = create_image_url(supplement_image, post.id, date_data, i) # s3에 객체 생성 후 url 리턴
            supplement_data = {
              'post' : post.id,
              'name' : supplement_name,
              'manufacturer' : list_input_supplement[i]['manufacturer'],
              # 'supplement_amount' : list_input_supplement[i]['supplement_amount'], # 일단 받지 않음.. 추후에 필요하면 추가!
              'image' : image_url,
            }
            supplement_create_serializer = SupplementSerializer(data=supplement_data)
            if supplement_create_serializer.is_valid():
              supplement_create_serializer.save()
            else:
              return Response(status=status.HTTP_400_BAD_REQUEST, data=supplement_create_serializer.errors)

      # 수정 & 추가 생성이 완료되었으면 deprecated consumption는 삭제
      try:
        deprecated_food_consumptions = Consumption.objects.filter(post=post.id, deprecated=True)
        deprecated_food_images = FoodImage.objects.filter(post=post.id, deprecated=True)
        deprecated_supplement_consumptions = SupplementConsmption.objects.filter(post=post.id, deprecated=True)
        # print(deprecated_consumptions)
        deprecated_food_consumptions.delete()
        deprecated_food_images.delete()
        deprecated_supplement_consumptions.delete()
        # print('deprecated consumptions 삭제 완료!')
      except:
        # print('deprecated consumptions가 존재하지 않습니다!')
        data = {
          "err_msg" : "deprecated consumptions가 존재하지 않습니다!" 
        }
        return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

      breakfast_consumptions = Consumption.objects.filter(post=post.id, meal_type='breakfast')
      breakfast_images = FoodImage.objects.filter(post=post.id, meal_type='breakfast')
      breakfast_images_queryset = breakfast_images.values('image')
      breakfast_images_list = []
      for i in range(len(breakfast_images_queryset)):
        breakfast_images_list.append(breakfast_images_queryset[i]['image'])
        
      lunch_consumptions = Consumption.objects.filter(post=post.id, meal_type='lunch')
      lunch_images = FoodImage.objects.filter(post=post.id, meal_type='lunch')
      lunch_images_queryset = lunch_images.values('image')
      lunch_images_list = []
      for i in range(len(lunch_images_queryset)):
        lunch_images_list.append(lunch_images_queryset[i]['image'])
      
      dinner_consumptions = Consumption.objects.filter(post=post.id, meal_type='dinner')
      dinner_images = FoodImage.objects.filter(post=post.id, meal_type='dinner')
      dinner_images_queryset = dinner_images.values('image')
      dinner_images_list = []
      for i in range(len(dinner_images_queryset)):
        dinner_images_list.append(dinner_images_queryset[i]['image'])

      snack_consumptions = Consumption.objects.filter(post=post.id, meal_type='snack')
      snack_images = FoodImage.objects.filter(post=post.id, meal_type='snack')
      snack_images_queryset = snack_images.values('image')
      snack_images_list = []
      for i in range(len(snack_images_queryset)):
        snack_images_list.append(snack_images_queryset[i]['image'])

      water_consumption = WaterConsumption.objects.get(post=post.id)
      supplement_consumption = SupplementConsmption.objects.filter(post=post.id)
      supplements = SupplementDetailSerializer(instance=supplement_consumption, many=True) # 직렬화

      data = {
        'meal' : {
          'breakfast' : {
            'foods' : breakfast_consumptions.values(),
            'image' : breakfast_images_list,
          },
          'lunch' : {
            'foods' : lunch_consumptions.values(),
            'image' : lunch_images_list,
          },
          'dinner' : {
            'foods' : dinner_consumptions.values(),
            'image' : dinner_images_list,
          },
          'snack' : {
            'foods' : snack_consumptions.values(),
            'image' : snack_images_list,
          }
        },
        'water' : water_consumption.amount,
        'supplement' : supplements.data,
        'post_id' : post.id,
      }
      return Response(data=data, status=status.HTTP_200_OK)
    else:
      data = {
        'error_msg' : '포스트가 존재하지 않습니다.'
      }
      return Response(status=status.HTTP_400_BAD_REQUEST, data=data)
