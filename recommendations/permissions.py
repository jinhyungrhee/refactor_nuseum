from rest_framework.permissions import BasePermission

class IsOwnerCheck(BasePermission):

  def has_object_permission(self, request, view, obj):
    # print(obj)
    # print(obj.target)
    # print(request.user.username)
    return obj.target == request.user.username