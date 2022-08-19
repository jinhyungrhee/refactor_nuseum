from rest_framework import serializers
from .models import Post, Consumption

class ConsumptionSerializer(serializers.ModelSerializer):
  class Meta:
    model = Consumption
    fields = '__all__'

  def create(self, validated_data):
    consumption = Consumption.objects.create(**validated_data)
    return consumption 

class PostSerializer(serializers.ModelSerializer):
  class Meta:
    model = Post
    exclude = ('author',)

  def create(self, validated_data):
    # TODO : 계산 + nutrient 객체 생성 로직 추가
    post = Post.objects.create(**validated_data)
    post.created_at = validated_data['created_at']
    return post

  # TODO : update 메서드 구현
  def update(self, instance, validated_data):
    pass