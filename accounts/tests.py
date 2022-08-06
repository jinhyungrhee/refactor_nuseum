from django.test import TestCase
from django.contrib.auth import get_user_model

class CustomUserTest(TestCase):
  def test_create_user(self):
    user = get_user_model().objects.create_user(
      username="사과",
      password="somepassword",
    )
    self.assertEqual(user.username, '사과')
    self.assertFalse(user.is_superuser)
    self.assertTrue(user.is_active)

  def test_Create_superuser(self):
    user = get_user_model().objects.create_superuser(
      username='superman',
      password='somepassword',
    )
    self.assertEqual(user.username, 'superman')
    self.assertTrue(user.is_superuser)
    self.assertTrue(user.is_active)