from django.apps import AppConfig

class ContentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'content'

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals
