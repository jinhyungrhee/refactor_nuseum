from importlib import import_module
from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
  username = models.CharField(max_length=15, unique=True, blank=True)

  def __str__(self):
    return self.username

# TODO: 중복 로그인 처리 로직 구현
# 현재 사용자의 세션을 저장하는 모델 객체 생성
class UserSession(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, editable=False)
  session_key = models.CharField(max_length=40, editable=False)
  created_at = models.DateTimeField(auto_now_add=True)


SessionStore = import_module(settings.SESSION_ENGINE).SessionStore

def kicked_my_other_sessions(sender, request, user, **kwars):
  for user_session in UserSession.objects.filter(user=user):
    session_key = user_session.session_key
    session = SessionStore(session_key)
    # session.delete()
    session['kicked'] = True
    session.save()
    user_session.delete()

  # method1
  session_key = request.session.session_key
  UserSession.objects.create(user=user, session_key=session_key)

  # method2 -> 제대로 동작 안하는듯?
  # if not request.session.session_key:
  #   request.session.create()
  # session_key = request.session.session_key

user_logged_in.connect(kicked_my_other_sessions, dispatch_uid='user_logged_in')