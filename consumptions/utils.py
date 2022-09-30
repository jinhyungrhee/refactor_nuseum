import base64
import boto3
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from .models import FoodImage, FoodConsumption, FoodPost, SupplementPost, WaterPost
from datetime import datetime, timedelta

# 식이분석 계산 로직
def nutrient_calculator(day_food_data, day_supplement_data, day_water_data, reporting_date):
  
  # print(data) # 쿼리셋

  energy, protein, fat, carbohydrate, dietary_fiber, magnesium, vitamin_a, vitamin_d, vitamin_b6,\
  folic_acid, vitamin_b12, tryptophan, dha_epa = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
  water = 0
  # method1 : dict
  category_mapper = {'채소':1, '샐러드':1, '나물':1, '과일':2, '과실류':2, '콩/두부':3, '두류':3, '통곡물':4, '버섯':5, '해조류':6, '견과':7, '고기/생선/달걀':8, '육류':8, '난류':8, '수산물':8, '어패류':8, '회류':8, '유제품':9, '발효유':9, '가공유':9, '가공두유':9 }

  # method2 : list
  # category_mapper = ['채소', '과일', '콩/두부', '통곡물', '버섯', '해조류', '견과', '고기/생선/달걀', '유제품']
  category_result = set([])

  # 음식 영양소 계산
  for elem in day_food_data:
    # print(f"FOOD ELEM : {elem}")
    # print(f"FOOD ELEM.FOOD : {elem.food}")
    # print(f"FOOD ELEM.FOOD.ENERGY : {elem.food.energy}")
    # print(f"FOOD ELEM.FOOD.CATEGORY : {elem.food.category}")
    # print(f"FOOD ELEM.AMOUNT : {elem.amount}")
    elem_amount = elem.amount
    '''
    food = Food.objects.get(id=elem['food_id'])
    # print(food, elem['amount'])
    '''
    energy += elem.food.energy * (elem_amount / 100)
    protein += elem.food.protein * (elem_amount / 100)
    fat += elem.food.fat * (elem_amount / 100)
    carbohydrate += elem.food.carbohydrate * (elem_amount / 100)
    dietary_fiber += elem.food.dietary_fiber * (elem_amount / 100)
    magnesium += elem.food.magnesium * (elem_amount / 100)
    vitamin_a += elem.food.vitamin_a * (elem_amount / 100)
    vitamin_d += elem.food.vitamin_d * (elem_amount / 100)
    vitamin_b6 += elem.food.vitamin_b6 * (elem_amount / 100)
    folic_acid += elem.food.folic_acid * (elem_amount / 100)
    vitamin_b12 += elem.food.vitamin_b12 * (elem_amount / 100)
    tryptophan += elem.food.tryptophan * (elem_amount / 100)
    dha_epa += elem.food.dha_epa * (elem_amount / 100)
    # method1 : dict
    for index, (key, val) in enumerate(category_mapper.items()):
      if key in elem.food.category:
        category_result.add(val)
    # # method2: list
    # for i in range(9):
    #   if category_mapper[i] in food.category:
    #     category_result.add(i+1)
    

  # 영양제 영양소 계산
  for elem in day_supplement_data:
    # print(f"SUPPLEMENT ELEM : {elem}")
    '''
    supplement = Supplement.objects.get(id=elem['supplement_id'])
    # print(food, elem['amount'])
    '''
    energy += elem.supplement.energy
    protein += elem.supplement.protein
    fat += elem.supplement.fat
    carbohydrate += elem.supplement.carbohydrate
    dietary_fiber += elem.supplement.dietary_fiber
    magnesium += elem.supplement.magnesium
    vitamin_a += elem.supplement.vitamin_a
    vitamin_d += elem.supplement.vitamin_d
    vitamin_b6 += elem.supplement.vitamin_b6
    folic_acid += elem.supplement.folic_acid
    vitamin_b12 += elem.supplement.vitamin_b12
    tryptophan += elem.supplement.tryptophan
    dha_epa += elem.supplement.dha_epa

  # 수분 섭취량 계산
  for elem in day_water_data:
    water += elem.amount
    
  sum_data = {
    'energy' : energy,
    'protein' : protein,
    'fat' : fat,
    'carbohydrate' : carbohydrate,
    'dietary_fiber' : dietary_fiber,
    'magnesium' : magnesium,
    'vitamin_a' : vitamin_a,
    'vitamin_d' : vitamin_d,
    'vitamin_b6' : vitamin_b6,
    'folic_acid' : folic_acid,
    'vitamin_b12' : vitamin_b12,
    'tryptophan' : tryptophan,
    'dha_epa' : dha_epa,
    'water_amount' :water,
    'day_count' : reporting_date,
    'category' : category_result, # 추가
  }

  return sum_data

# 이미지 처리 로직
def create_image_url(image_string, post_id, date_data, username):
  
  year = date_data.strftime('%Y')
  month = date_data.strftime('%m')
  day = date_data.strftime('%d')
  header, data = image_string.split(';base64,')
  data_format, ext = header.split('/')
  try:
    # supplement_post = SupplementPost.objects.get(id=post_id)
    image_data = base64.b64decode(data) # 이미지 파일 생성
    s3r = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    key = "%s"%(f'{year}/{month}/{day}')
    s3r.Bucket(settings.AWS_STORAGE_BUCKET_NAME).put_object(Key=key+'/%s'%(f'{username}_supplement_{post_id}.{ext}'), Body=image_data, ContentType='jpg')
    aws_url = f'{settings.IMAGE_URL}/{year}/{month}/{day}/{username}_supplement_{post_id}.{ext}'
    # supplement_post.image = aws_url
    # supplement_post.save()

  except TypeError:
    data = {
      "err_msg" : "invalid_image"
    }
    return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
  
  return aws_url
  # return supplement_post


def delete_image(image_name):
  try:
    key = image_name.split('jinhyung.test.aws/')[1] # 파일명
    # print(key)
    s3_client = boto3.client(
      's3',
      aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
    
  except TypeError:
    data = {
      "err_msg" : "invalid_image"
    }
    return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


# date validation 처리 (date -> int_date)
def convert_to_int_date(date):
  # print("DATE 검사 실행!!!")
  if date is None:
    return None
  elif len(date) != 13:
    return None
  else:
    # 예외처리
    try:
      int_date = int(date)
      return int_date
    except ValueError:
      return None

# 제출 날짜 체크(counting)
def count_reporting_date(today_date, author, type):
  decreasing_date = today_date
  if type == "day":
    # print(FoodConsumption.objects.filter(post__author=author, post__created_at=decreasing_date)) # filter에서 fk 필드에 접근하는 법!
    if FoodConsumption.objects.filter(post__author=author, post__created_at=decreasing_date).exists() or SupplementPost.objects.filter(author=author, created_at=decreasing_date).exists():
      count = 1
    else:
      count = 0

  elif type == "week":
    count = 0
    for i in range(7):
      # print(decreasing_date)
      if FoodConsumption.objects.filter(post__author=author, post__created_at=decreasing_date).exists() or SupplementPost.objects.filter(author=author, created_at=decreasing_date).exists():
        count += 1
      decreasing_date -= timedelta(1)

  elif type == "month":
    count = 0
    for i in range(31):
      # print(decreasing_date)
      if FoodConsumption.objects.filter(post__author=author, post__created_at=decreasing_date).exists() or SupplementPost.objects.filter(author=author, created_at=decreasing_date).exists():
        count += 1
      decreasing_date -= timedelta(1)
  # print(count)
  return count
