from rest_framework.permissions import BasePermission

from consumptions.models import FoodConsumption, FoodImage, SupplementConsumption

MEAL_TYPE = ["breakfast", "lunch", "dinner", "snack"]

class IsOwner(BasePermission):

  def has_object_permission(self, request, view, obj):
    # print(obj)
    # print(obj.post)
    # print(obj.post.author)
    return obj.post.author == request.user

class IsOwnerorAdmin(BasePermission):

  def has_object_permission(self, request, view, obj):
    if type(obj) == FoodConsumption or type(obj) == FoodImage or type(obj) == SupplementConsumption:
      return obj.post.author == request.user or request.user.is_superuser or request.user.is_staff # 스태프 권한 추가
    else: # WaterPost
      return obj.author == request.user or request.user.is_superuser or request.user.is_staff

    # print(type(obj) == FoodConsumption)
    '''
    if obj.type == "supplement" or obj.type == "water": # xxxPOST
      return obj.author == request.user or request.user.is_superuser
    else: # breakfast, lunch, dinner, snack
      return obj.post.author == request.user or request.user.is_superuser
    '''