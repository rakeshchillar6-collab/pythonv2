# apis/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from content.models import Post
from core.models import User

class IsOwnerOrAdmin(BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the post or an admin.
        user: User = request.user
        return obj.author == user or user.has_role('admin')
