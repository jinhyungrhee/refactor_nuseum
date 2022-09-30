from django.db import models
from accounts.models import User

class Question(models.Model):
  title = models.CharField(max_length=100, blank=True)
  content = models.TextField()
  # TODO : 이미지 필드 1개
  author = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
  created_at = models.DateTimeField(auto_now_add=True) # dt로 바꿔야 정상 동작!
  updated_at = models.DateTimeField(auto_now=True)
  # 답변 완료 기능
  is_answered = models.BooleanField(default=False)

  def __str__(self):
    return f"[{self.pk}] {self.title}::{self.author}"


class Answer(models.Model):
  question = models.ForeignKey(Question, on_delete=models.CASCADE)
  author = models.ForeignKey(User, on_delete=models.CASCADE)
  content = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  @property
  def short_content(self):
    return self.content[:10]

  def __str__(self):
    return f"{self.author}::{self.content[:30]}"