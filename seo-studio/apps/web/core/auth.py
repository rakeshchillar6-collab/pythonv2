# core/auth.py
from functools import wraps
from typing import Callable, Type
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from rest_framework.permissions import BasePermission
from rest_framework.views import APIView
from .models import User

def require_roles(*roles: str) -> Callable:
    """
    A decorator for Django views that checks if a user has one of the specified roles.
    Redirects to a permission denied page if the user is not authenticated or
    does not have the required role.
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if not request.user.is_authenticated:
                raise PermissionDenied("You must be logged in to view this page.")

            # Type hint for static analysis
            user: User = request.user
            if not user.has_role(*roles) and not user.is_superuser:
                raise PermissionDenied("You do not have permission to perform this action.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


class RolePermission(BasePermission):
    """
    A DRF permission class that checks if a user has one of the specified roles.

    Usage in a ViewSet:
    `permission_classes = [IsAuthenticated, RolePermission.of('admin', 'editor')]`
    """
    required_roles: list[str] = []

    @classmethod
    def of(cls, *roles: str) -> Type["RolePermission"]:
        """
        Factory method to create a permission class with specific roles.
        """
        return type(
            "RolePermission",
            (cls,),
            {"required_roles": list(roles)},
        )

    def has_permission(self, request: HttpRequest, view: APIView) -> bool:
        """
        Check if the user has the required role.
        """
        user: User = request.user
        return user.is_authenticated and (
            user.has_role(*self.required_roles) or user.is_superuser
        )
