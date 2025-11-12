# tests/conftest.py
import pytest
from core.models import User

@pytest.fixture
def test_password():
   return 'strong-password'

@pytest.fixture
def create_user(db, django_user_model, test_password):
   def make_user(**kwargs):
       kwargs['password'] = test_password
       if 'email' not in kwargs:
           kwargs['email'] = 'test@example.com'
       return django_user_model.objects.create_user(**kwargs)
   return make_user

@pytest.fixture
def api_client():
   from rest_framework.test import APIClient
   return APIClient()

@pytest.fixture
def authenticated_client(api_client, create_user):
    user = create_user()
    api_client.force_authenticate(user=user)
    return api_client
