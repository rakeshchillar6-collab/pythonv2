# common/models.py
import uuid
from django.db import models

class BaseModel(models.Model):
    """
    An abstract base model that provides self-updating
    `created_at` and `updated_at` fields.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']
