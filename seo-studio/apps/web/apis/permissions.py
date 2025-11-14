# apis/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from content.models import Post
from core.models import User

class IsOwnerOrAdmin(BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request.
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object or an admin.
        user: User = request.user
        if not user.role:
            return False

        is_admin = 'admin' in user.role.permissions or '*' in user.role.permissions

        # Check if the object has an 'author' or 'user' attribute.
        if hasattr(obj, 'author'):
            return obj.author == user or is_admin
        if hasattr(obj, 'user'):
            return obj.user == user or is_admin

        return is_admin
