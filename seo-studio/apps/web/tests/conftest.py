# tests/conftest.py
import pytest
from core.models import User

@pytest.fixture
def test_password():
   return 'strong-password'

from core.models import Role

@pytest.fixture
def create_user(db, django_user_model, test_password):
   def make_user(**kwargs):
       kwargs['password'] = test_password
       if 'email' not in kwargs:
           kwargs['email'] = 'test@example.com'

       roles = kwargs.pop('roles', [])
       user = django_user_model.objects.create_user(**kwargs)
       if roles:
           user.roles.set(roles)
       return user
   return make_user

@pytest.fixture
def create_role(db):
    def make_role(**kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = 'Test Role'
        if 'slug' not in kwargs:
            kwargs['slug'] = 'test-role'
        return Role.objects.create(**kwargs)
    return make_role

@pytest.fixture
def api_client():
   from rest_framework.test import APIClient
   return APIClient()

@pytest.fixture
def authenticated_client(api_client, create_user):
    user = create_user()
    api_client.force_authenticate(user=user)
    return api_client
