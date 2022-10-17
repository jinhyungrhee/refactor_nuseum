from rest_framework import serializers
from .models import Notice

class NoticeSerializer(serializers.ModelSerializer):
  class Meta:
    model = Notice
    fields = '__all__'
    # exclude = ('user_list',)

  def create(self, validated_data):
    notice = Notice.objects.create(**validated_data)
    return notice

  def update(self, instance, validated_data):
      instance.title = validated_data.get('title', instance.title)
      instance.content = validated_data.get('content', instance.content)
      instance.save()
      return instance

class CustomNoticeSerializer(serializers.Serializer):
  id = serializers.IntegerField()
  clicked = serializers.IntegerField()