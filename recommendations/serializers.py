from rest_framework import serializers
from .models import Recommendation
from datetime import timedelta

class RecommendationSerializer(serializers.ModelSerializer):
  class Meta:
    model = Recommendation
    fields = '__all__'

  def create(self, validated_data):
    notice = Recommendation.objects.create(**validated_data)
    return notice

  def update(self, instance, validated_data):
      instance.type1 = validated_data.get('type1', instance.type1)
      instance.type2 = validated_data.get('type2', instance.type2)
      instance.type3 = validated_data.get('type3', instance.type3)
      instance.type4 = validated_data.get('type4', instance.type4)
      instance.type5 = validated_data.get('type5', instance.type5)
      instance.type6 = validated_data.get('type6', instance.type6)
      instance.type7 = validated_data.get('type7', instance.type7)
      instance.type8 = validated_data.get('type8', instance.type8)
      instance.type9 = validated_data.get('type9', instance.type9)
      instance.type10 = validated_data.get('type10', instance.type10)
      instance.type11 = validated_data.get('type11', instance.type11)
      instance.type12 = validated_data.get('type12', instance.type12) # 주의 추가
      instance.comment = validated_data.get('comment', instance.comment) # 코멘트 추가
      instance.save()
      return instance

class RecommendationListSerializer(serializers.ModelSerializer):
  start_date = serializers.SerializerMethodField()
  # ordering = serializers.SerializerMethodField()
  title = serializers.SerializerMethodField()
  class Meta:
    model = Recommendation
    fields = ('id', 'target', 'created_at', 'start_date', 'title')

  def get_start_date(self, obj):
    # print(obj.created_at - timedelta(days=6))
    return obj.created_at - timedelta(days=6)

  def get_ordering(self, obj):
    count = Recommendation.objects.filter(pk__lte=obj.pk, target=obj.target).count()
    return count

  def get_title(self, obj):
    count = self.get_ordering(obj)
    start_date = self.get_start_date(obj)
    # return f'{obj.target}의 {count}번째 식이추천 내용입니다. ({str(start_date).split(" ")[0]}~{str(obj.created_at).split(" ")[0]})'
    return f'[{obj.target}]{start_date.strftime("%m/%d")} ~ {obj.created_at.strftime("%m/%d")} 식이추천 내용입니다.'
    
class RecommendationDetailSerializer(serializers.Serializer):
  type = serializers.CharField()
  main = serializers.CharField()
  list = serializers.ListField()
  order = serializers.CharField() # 중요도