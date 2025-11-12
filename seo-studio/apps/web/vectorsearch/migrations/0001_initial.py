# vectorsearch/migrations/0001_initial.py
from django.db import migrations
from pgvector.django import VectorExtension

class Migration(migrations.Migration):
    """
    This migration enables the pgvector extension in the database.
    It must be the first migration in this app.
    """
    initial = True

    dependencies = []

    operations = [
        VectorExtension(),
    ]
