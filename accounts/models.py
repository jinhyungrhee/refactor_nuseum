from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
  username = models.CharField(max_length=15, unique=True, blank=True)

  def __str__(self):
    return self.username
