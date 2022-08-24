from rest_framework import serializers
from .models import Consumption, WaterConsumption, FoodImage
from django.conf import settings
from foods.models import Food
from posts.models import Post
from datetime import datetime
import base64

class ConsumptionSerializer(serializers.ModelSerializer):
  class Meta:
    model = Consumption
    fields = '__all__'

  def create(self, validated_data):
    print(validated_data)
    consumption = Consumption.objects.create(**validated_data)
    return consumption 

  def update(self, instance, validated_data):
    # print(validated_data)
    instance.post = validated_data.get("post", instance.post) # None?
    instance.food = validated_data.get("food", instance.food) # None?
    instance.amount = validated_data.get("amount", instance.amount) # None?
    instance.meal_type = validated_data.get("meal_type", instance.meal_type) # None?
    instance.img1 = validated_data.get("img1", instance.img1)
    instance.img2 = validated_data.get("img2", instance.img2)
    instance.img3 = validated_data.get("img3", instance.img3)
    instance.deprecated = validated_data.get("deprecated", instance.deprecated)
    instance.save()

    return instance

class WaterSerializer(serializers.ModelSerializer):
  class Meta:
    model = WaterConsumption
    fields = '__all__'

  def create(self, validated_data):
    water_consumption = WaterConsumption.objects.create(**validated_data)
    return water_consumption

  def update(self, instance, validated_data):
    instance.post = validated_data.get("post", instance.post)
    instance.amount = validated_data.get("amount", instance.amount)
    # instance.deprecated = validated_data.get("deprecated", instance.deprecated)
    instance.save()
    return instance

# 이미지 처리
class ImageDecodeSerializer(serializers.ModelSerializer):

  def create(self, validated_data):
    # post = Post.objects.create(**validated_data) # 수정 필요 (기존에 생성된 post 모델의 id를 넣어야함!)**
    post = self.context.get("post")
    print("POST INSTANCE:", post)
    curr_time = datetime.now()
    year = curr_time.strftime('%Y')
    month = curr_time.strftime('%m')
    day = curr_time.strftime('%d')

    # 이미지 디코딩
    bulk_list = []
    num = 1
    # print(self.context.get("images")) -> 리스트([]) 형태여야 함!
    # base64로 인코딩된 이미지 불러움
    for image_string in self.context.get("images"): # view에서 보낸 context에서 가져옴*
      header, data = image_string.split(';base64,')
      # print(header, data)
      data_format, ext = header.split('/')
      try:
        image_data = base64.b64decode(data) # 이미지 생성
        # image_root = settings.MEDIA_ROOT + "\\post\\images\\2022\\08\\23\\" + str(post.id) + "_" + str(num) + "." + ext
        # image_root = settings.MEDIA_ROOT + f'\\post\\images\\{year}\\{month}\\{day}\\' + str(post.id) + "_" + str(num) + "." + ext
        image_root = settings.MEDIA_ROOT + "\\" + str(post.id) + "_" + str(num) + "." + ext
        print(image_root)
        # 파일 생성 코드 왜 안되는지 체크!
        # if not os.path.isdir(image_root):
        #     os.makedirs(image_root)
        with open(image_root, 'wb') as f:
          f.write(image_data)
          bulk_list.append(FoodImage(post=post.id, image=f'{post.id}_{num}.{ext}'))
        num += 1
      except TypeError:
        self.fail('invalid_image')
      
    images = FoodImage.objects.bulk_create(bulk_list)
    # print(images)

    return post
  
  class Meta:
    model = FoodImage
    fields = '__all__'