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