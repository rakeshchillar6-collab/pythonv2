# schema_builder/apps.py
from django.apps import AppConfig

class SchemaBuilderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'schema_builder'
