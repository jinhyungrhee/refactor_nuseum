from django.db import models
from accounts.models import User
from foods.models import Food

class Post(models.Model):
  author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
  created_at = models.DateTimeField(blank=True) # datetimefield 사용해야 범위로 가져올 수 있음!
  updated_at = models.DateTimeField(auto_now=True)
  # 이미지 여러 개 올리는법?

  def __str__(self):
    return f'[{self.pk}] {self.author}\'s post :: {self.created_at}'