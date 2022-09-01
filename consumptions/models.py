from django.db import models
from posts.models import Post
from foods.models import Food, Supplement

# POST와 FOOD를 연결하는 중간 테이블(many-to-many)
class Consumption(models.Model):
  MEAL_CHOICES = (
    ('breakfast', '아침'),
    ('lunch', '점심'),
    ('dinner', '저녁'),
    ('snack', '간식'),
  )

  post = models.ForeignKey(Post, on_delete=models.CASCADE)
  food = models.ForeignKey(Food, on_delete=models.CASCADE)
  amount = models.IntegerField(default=0)
  meal_type = models.CharField(max_length=12, choices=MEAL_CHOICES, default=' ') 
  deprecated = models.BooleanField(default=False)

  def __str__(self):
    return f'[post_no.{self.post.id}]{self.food}, {self.amount}, {self.meal_type}'

class WaterConsumption(models.Model):
  post = models.ForeignKey(Post, on_delete=models.CASCADE)
  amount = models.IntegerField(default=0) # 입력 받은 값으로 계속 수정되게만 구현하면 됨! (필수 입력X)

  def __str__(self):
    return f'[post_no.{self.post.id}] {self.amount}'

class SupplementConsmption(models.Model):
  post = models.ForeignKey(Post, on_delete=models.CASCADE)
  # supplement = models.IntegerField(default=0) # FK 안쓰는 경우
  supplement = models.ForeignKey(Supplement, on_delete=models.SET_NULL, blank=True, null=True) # 나중에 DB에 인스턴스 생성 후 연결
  name = models.CharField(max_length=100)
  manufacturer = models.CharField(max_length=100)
  amount = models.IntegerField(default=0) # 임시 필드
  image = models.CharField(max_length=250, blank=True)  # S3 주소 저장
  deprecated = models.BooleanField(default=False) # 삭제 로직 구현

  def __str__(self):
    return f'[post_no.{self.post.id}] {self.name}'

class FoodImage(models.Model):
  MEAL_CHOICES = (
    ('breakfast', '아침'),
    ('lunch', '점심'),
    ('dinner', '저녁'),
    ('snack', '간식'),
  )
  post = models.ForeignKey(Post, on_delete=models.CASCADE)
  # post = models.IntegerField(default=0)
  # image = models.ImageField(upload_to='post/images/%Y/%m/%d', blank=True)
  image = models.CharField(max_length=250, blank=True)
  meal_type = models.CharField(max_length=12, choices=MEAL_CHOICES, default=' ')
  deprecated = models.BooleanField(default=False)

  def __str__(self):
    return f'[post_no.{self.post.id}] {self.image} :: {self.id}'
  