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


class Organization(BaseModel):
    """
    Represents a company or a top-level entity.
    Each organization can have multiple sites and users.
    """
    name = models.CharField(max_length=200, unique=True)

    def __str__(self) -> str:
        return self.name

class Site(BaseModel):
    """
    Represents a website or project within an organization.
    All content and settings are scoped to a site.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='sites')
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=255, unique=True)

    class Meta:
        unique_together = ('organization', 'name')

    def __str__(self) -> str:
        return f"{self.name} ({self.domain})"

class Role(BaseModel):
    """
    Represents a user role within an organization.
    Permissions are stored as a JSON list of strings.
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    permissions = models.JSONField(default=list, help_text="List of permission strings, e.g., 'content.create'. Use '*' for all permissions.")

    class Meta:
        unique_together = ('organization', 'name')

    def __str__(self) -> str:
        return self.name

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model. Users are scoped to an organization and have a single role.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)

    # Each user belongs to one organization and has one role.
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, related_name='users', null=True, blank=True)

    is_staff = models.BooleanField(default=False, help_text="Designates whether the user can log into the Django admin site.")
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
