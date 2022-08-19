from rest_framework import serializers
from .models import Food

class FoodSerializer(serializers.ModelSerializer):

  class Meta:
    model = Food
    fields = '__all__'

class FoodNameSerializer(serializers.ModelSerializer):

  class Meta:
    model = Food
    fields = ['name']