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