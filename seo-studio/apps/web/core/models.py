# core/models.py
import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from common.models import BaseModel

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None # We will use email as the unique identifier
    email = models.EmailField('email address', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

# Stub models for RBAC
class Role(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField('Permission', blank=True)

    def __str__(self):
        return self.name

class Permission(BaseModel):
    name = models.CharField(max_length=100, unique=True) # e.g., 'post.create', 'post.delete'
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Stub models for multi-tenancy/multi-site
class Organization(BaseModel):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_organizations')
    members = models.ManyToManyField(User, related_name='organizations')

    def __str__(self):
        return self.name

class SiteProfile(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=200) # e.g., "My Blog"
    domain = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.name} ({self.domain})"
