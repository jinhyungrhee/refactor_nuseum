from django.db import models

class Category(models.Model):
  name = models.CharField(max_length=30)

  def __str__(self):
    return self.name

  class Meta:
    verbose_name_plural = 'categories'

class Food(models.Model):
  name = models.CharField(max_length=200)
  category = models.ManyToManyField(Category, blank=True) # 중간테이블 생성 필요?

  energy = models.FloatField(default=0.0)
  protein = models.FloatField(default=0.0)
  fat = models.FloatField(default=0.0)
  carbohydrate = models.FloatField(default=0.0)
  
  dietary_fiber = models.FloatField(default=0.0)
  magnesium = models.FloatField(default=0.0)
  vitamin_a = models.FloatField(default=0.0)
  vitamin_d = models.FloatField(default=0.0)
  vitamin_b6 = models.FloatField(default=0.0)
  folic_acid = models.FloatField(default=0.0)
  vitamin_b12 = models.FloatField(default=0.0)
  tryptophan = models.FloatField(default=0.0)
  dha_epa = models.FloatField(default=0.0)

  classifier = models.IntegerField(default=0)

  def __str__(self):
    # return f'{self.pk}, {self.name}' # 프론트에서 pk가 필요하면 이것 사용
    return f'{self.name}' # 그렇지 않으면 이름만 사용
