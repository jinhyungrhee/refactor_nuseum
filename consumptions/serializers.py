from rest_framework import serializers
from .models import Consumption, WaterConsumption, FoodImage
from django.conf import settings
from foods.models import Food
from posts.models import Post
from datetime import datetime
import base64
import boto3

class ConsumptionSerializer(serializers.ModelSerializer):
  class Meta:
    model = Consumption
    fields = '__all__'

  def create(self, validated_data):
    # print(validated_data)
    consumption = Consumption.objects.create(**validated_data)
    return consumption 

  def update(self, instance, validated_data):
    # print(validated_data)
    instance.post = validated_data.get("post", instance.post) # None?
    instance.food = validated_data.get("food", instance.food) # None?
    instance.amount = validated_data.get("amount", instance.amount) # None?
    instance.meal_type = validated_data.get("meal_type", instance.meal_type) # None?
    # instance.img1 = validated_data.get("img1", instance.img1)
    # instance.img2 = validated_data.get("img2", instance.img2)
    # instance.img3 = validated_data.get("img3", instance.img3)
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
    post = self.context.get("post")
    meal_type = self.context.get("meal_type")
    date_data = self.context.get("date")
    num = self.context.get("num")

    year = date_data.strftime('%Y')
    month = date_data.strftime('%m')
    day = date_data.strftime('%d')
    # print("context.get(\"images\") LOG:", self.context.get("images")) 
    image_string = self.context.get("images") # String으로 들어옴! -> 시간 단축!
    header, data = image_string.split(';base64,')
    # header, data = image_string[num].split(';base64,') # 리스트째로 들어옴!
    data_format, ext = header.split('/')
    try:
      image_data = base64.b64decode(data) # 이미지 파일 생성
      s3r = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
      key = "%s"%(f'{year}/{month}/{day}')
      s3r.Bucket(settings.AWS_STORAGE_BUCKET_NAME).put_object(Key=key+'/%s'%(f'{post.id}_{meal_type}_{num}.{ext}'), Body=image_data, ContentType='jpg')
      aws_url = f'{settings.IMAGE_URL}/{year}/{month}/{day}/{post.id}_{meal_type}_{num}.{ext}'
      FoodImage.objects.create(post=post, image=aws_url, meal_type=meal_type) # 이미지 객체 생성하여 DB에 저장

    except TypeError:
      self.fail('invalid_image')
      
    return post

  def update(self, instance, validated_data):
    instance.post = validated_data.get("post", instance.post)
    instance.image = validated_data.get("image", instance.image)
    instance.meal_type = validated_data.get("meal_type", instance.meal_type)
    instance.deprecated = validated_data.get("deprecated", instance.deprecated)
    # instance.deprecated = validated_data.get("deprecated", instance.deprecated)
    instance.save()
    return instance
  
  class Meta:
    model = FoodImage
    fields = ('image', 'meal_type', 'deprecated')
    # fields = '__all__'