from rest_framework import serializers
from .models import Consumption
from foods.models import Food

class ConsumptionSerializer(serializers.ModelSerializer):
  class Meta:
    model = Consumption
    fields = '__all__'

  def create(self, validated_data):
    consumption = Consumption.objects.create(**validated_data)
    return consumption 