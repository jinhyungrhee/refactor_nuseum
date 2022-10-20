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
  type12 = models.CharField(max_length=200, default='', null=True, blank=True) # 주의
  comment = models.TextField(default='', null=True, blank=True) # 코멘트
  # created_at = models.DateTimeField(auto_now_add=True)
  created_at = models.DateTimeField(blank=True, null=True)

  def __str__(self):
    return f'[{self.pk}] {self.target}\'s 추천식품 ({str(self.created_at).split()[0]} 작성)'

  def get_type(self, num):
    if num == 1: # 과일
      return self.type1
    elif num == 2: # 채소
      return self.type2
    elif num == 3: # 콩/두부
      return self.type3
    elif num == 4: # 통곡물
      return self.type4
    elif num == 5: # 버섯
      return self.type5
    elif num == 6: # 해조류
      return self.type6
    elif num == 7: # 견과
      return self.type7
    elif num == 8: # 고기/생선/달걀
      return self.type8
    elif num == 9: # 유제품
      return self.type9
    elif num == 10: # 가공식품
      return self.type10
    elif num == 11: # 영양제
      return self.type11
    elif num == 12: # 주의
      return self.type12