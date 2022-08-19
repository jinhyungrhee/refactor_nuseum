from rest_framework import serializers
from .models import Post
from foods.models import Food

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

# 일단 하루 영양 집계 시리얼라이저 -> consumption으로 이동!
# class NutrientSumSerializer(serializers.ModelSerializer):

#   class Meta:
#     model = Food
#     exclude = ('name', 'classifier',)