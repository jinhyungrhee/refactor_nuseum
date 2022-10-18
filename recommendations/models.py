from django.db import models

# Create your models here.
class Recommendation(models.Model):
  target = models.CharField(max_length=30)
  type1 = models.CharField(max_length=200, default='', null=True, blank=True)
  type2 = models.CharField(max_length=200, default='', null=True, blank=True)
  type3 = models.CharField(max_length=200, default='', null=True, blank=True)
  type4 = models.CharField(max_length=200, default='', null=True, blank=True)
  type5 = models.CharField(max_length=200, default='', null=True, blank=True)
  type6 = models.CharField(max_length=200, default='', null=True, blank=True)
  type7 = models.CharField(max_length=200, default='', null=True, blank=True)
  type8 = models.CharField(max_length=200, default='', null=True, blank=True)
  type9 = models.CharField(max_length=200, default='', null=True, blank=True)
  type10 = models.CharField(max_length=200, default='', null=True, blank=True)
  type11 = models.CharField(max_length=200, default='', null=True, blank=True)
  # created_at = models.DateTimeField(auto_now_add=True)
  created_at = models.DateTimeField(blank=True, null=True)

  def __str__(self):
    return f'[{self.pk}] {self.target}\'s 추천식품 ({str(self.created_at).split()[0]} 작성)'

  def get_type(self, num):
    if num == 1:
      return self.type1
    elif num == 2:
      return self.type2
    elif num == 3:
      return self.type3
    elif num == 4:
      return self.type4
    elif num == 5:
      return self.type5
    elif num == 6:
      return self.type6
    elif num == 7:
      return self.type7
    elif num == 8:
      return self.type8
    elif num == 9:
      return self.type9
    elif num == 10:
      return self.type10
    elif num == 11:
      return self.type11