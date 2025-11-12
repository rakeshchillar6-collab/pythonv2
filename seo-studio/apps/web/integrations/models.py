# integrations/models.py
from django.db import models
from common.models import BaseModel
from django.utils.translation import gettext_lazy as _

class Connector(BaseModel):
    """
    Represents a connection to an external service like Google Search Console,
    Google Analytics, etc.
    """
    class ConnectorType(models.TextChoices):
        GSC = 'GSC', _('Google Search Console')
        GA4 = 'GA4', _('Google Analytics 4')
        PROGRAMMABLE_SEARCH = 'PSE', _('Programmable Search Engine')
        OLLAMA = 'OLLAMA', _('Ollama')
        STABLE_DIFFUSION = 'SD', _('Stable Diffusion')

    class ConnectorStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        DISABLED = 'DISABLED', _('Disabled')
        ERROR = 'ERROR', _('Error')

    type = models.CharField(
        max_length=10,
        choices=ConnectorType.choices,
        unique=True, # Assuming one connector of each type for now
        help_text="The type of the external service."
    )
    status = models.CharField(
        max_length=10,
        choices=ConnectorStatus.choices,
        default=ConnectorStatus.DISABLED,
        help_text="The current status of the connector."
    )
    credentials_encrypted = models.TextField(
        blank=True,
        help_text="Encrypted credentials for the service (e.g., API key, OAuth token)."
    )
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last successful data sync."
    )
    last_error_message = models.TextField(
        blank=True,
        help_text="Details of the last error encountered."
    )
    quota_used = models.PositiveIntegerField(default=0)
    quota_total = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return self.get_type_display()

    @property
    def is_healthy(self) -> bool:
        """A connector is healthy if it is not in an error state."""
        return self.status != self.ConnectorStatus.ERROR
