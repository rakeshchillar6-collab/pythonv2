# core/models.py
import uuid
from typing import ClassVar
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from common.models import BaseModel

class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> "User":
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class Role(BaseModel):
    """
    Represents a user role, which can be assigned to users to grant permissions.
    For simplicity, we are not using Django's built-in Permission model directly
    but defining roles with slugs that can be checked in code.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, help_text="A unique slug for the role, e.g., 'admin', 'editor'.")

    def __str__(self) -> str:
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email for authentication.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    roles = models.ManyToManyField(Role, blank=True, related_name="users")

    is_staff = models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.")
    is_active = models.BooleanField(default=True, help_text="Designates whether this user should be treated as active.")
    date_joined = models.DateTimeField(auto_now_add=True)

    objects: ClassVar[UserManager] = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return self.email

    def has_role(self, *roles: str) -> bool:
        """Checks if the user has any of the specified roles (by slug)."""
        return self.roles.filter(slug__in=roles).exists()
