from rest_framework import serializers
from .models import Food, Supplement

class FoodSerializer(serializers.ModelSerializer):

  class Meta:
    model = Food
    fields = '__all__'

class SupplementSerializer(serializers.ModelSerializer):

  class Meta:
    model = Supplement
    fields = '__all__'