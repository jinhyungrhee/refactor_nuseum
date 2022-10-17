from django.db import models

# Create your models here.
class Notice(models.Model):
  title = models.CharField(max_length=100, blank=True)
  content = models.TextField()
  user_list = models.TextField(default='', null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)
  
  def __str__(self):
    return f'[{self.id}] {self.content}'
