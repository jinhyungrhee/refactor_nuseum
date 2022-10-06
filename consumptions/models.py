from django.db import models
# from django.contrib.auth.models import User
from accounts.models import User
from foods.models import Food, Supplement

# BASE
class BasePost(models.Model):
  TYPE_CHOICES = (
    ('breakfast', '아침'),
    ('lunch', '점심'),
    ('dinner', '저녁'),
    ('snack', '간식'),
    ('supplement', '영양제'),
    ('water', '물'),
  )
  type = models.CharField(max_length=12, choices=TYPE_CHOICES, default=' ')
  created_at = models.DateTimeField(blank=True, null=True) # datetimefield 사용해야 범위로 가져올 수 있음!
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    abstract = True

# FOOD
class FoodPost(BasePost):
  author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

  def __str__(self):
    return f'[{self.pk}]{self.created_at}||{self.author}\'s {self.type}' # 이래도 나중에 성능 괜찮을까..??
    # return f'[{self.pk}]{str(self.created_at)[:10]}|{self.author}\'s {self.type}' # 이래도 나중에 성능 괜찮을까..??

class FoodImage(models.Model):
  post = models.ForeignKey(FoodPost, on_delete=models.CASCADE, null=True, blank=True)
  image = models.CharField(max_length=250, blank=True)
  def __str__(self):
    return f'<{self.pk}>[post_no.{self.post.id}]{self.image}'
    # return f'[post_no.{self.post}]{self.image}'

class FoodConsumption(models.Model):
  post = models.ForeignKey(FoodPost, on_delete=models.CASCADE, null=True, blank=True)
  food = models.ForeignKey(Food, on_delete=models.CASCADE, null=True, blank=True)
  amount = models.IntegerField(default=0)
  def __str__(self):
    # return f'<{self.pk}>[post_no.{self.post.id}]'
    return f'<{self.pk}>[post_no.{self.post.id}]{self.food.name}, {self.amount}'

# SUPPLEMENT
# class SupplementPost(BasePost):
#   author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

#   def __str__(self):
#     return f'[{self.pk}] {self.author}\'s post :: {self.created_at}'
'''
class SupplementPost(BasePost):
  # post = models.ForeignKey(SupplementPost, on_delete=models.CASCADE, null=True, blank=True)
  author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
  supplement = models.ForeignKey(Supplement, on_delete=models.SET_NULL, blank=True, null=True, default=1) # 나중에 DB에 인스턴스 생성 후 연결
  name = models.CharField(max_length=100, default='')
  manufacturer = models.CharField(max_length=100, default='')
  # amount = models.IntegerField(default=0) # 필요없을 듯
  image = models.CharField(max_length=250, blank=True)  # S3 주소 저장

  def __str__(self):
    return f'[{self.pk}] {self.author}\'s post :: {self.created_at}'
'''

# Supplement 수정
class SupplementPost(BasePost):
  author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

  def __str__(self):
    return f'[{self.pk}] {self.author}\'s post :: {self.created_at}'

class SupplementConsumption(models.Model):
  post = models.ForeignKey(SupplementPost, on_delete=models.CASCADE, null=True, blank=True)
  supplement = models.ForeignKey(Supplement, on_delete=models.SET_NULL, blank=True, null=True, default=1) # 나중에 DB에 인스턴스 생성 후 연결
  name = models.CharField(max_length=100)
  manufacturer = models.CharField(max_length=100)
  image = models.CharField(max_length=250, blank=True)  # S3 주소 저장
  def __str__(self):
    return f'<{self.pk}>[pno.{self.post.id} - {self.post.author}]{self.name}, {self.manufacturer}'


# WATER
class WaterPost(BasePost):
  author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
  amount = models.IntegerField(default=0)

  def __str__(self):
    return f'[{self.pk}]{self.author}\'s post :: {self.amount} ({self.created_at})'

