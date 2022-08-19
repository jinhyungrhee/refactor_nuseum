from django.db import models
from posts.models import Post
from foods.models import Food

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
  # 분리 가능한지 후에 check => 일단은 url을 저장하는 Charfield()로 사용해야 할듯!
  img1 = models.ImageField(upload_to='post/images/%Y/%m/%d', blank=True)
  img2 = models.ImageField(upload_to='post/images/%Y/%m/%d', blank=True)
  img3 = models.ImageField(upload_to='post/images/%Y/%m/%d', blank=True)

  def __str__(self):
    return f'[post_no.{self.post.id}]{self.food}, {self.amount}, {self.meal_type}'