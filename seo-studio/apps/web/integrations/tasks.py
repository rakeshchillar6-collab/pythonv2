# integrations/tasks.py
import logging
from celery import shared_task
from .models import Connector

logger = logging.getLogger(__name__)

@shared_task
def update_statuses():
    """
    A periodic task to update the status of external connectors.
    This is a stub for now. In a real scenario, it would iterate over
    connectors, check their health, and update their status in the DB.
    """
    logger.info("Running periodic task: update_statuses...")
    # Example logic:
    # for connector in Connector.objects.filter(status=Connector.ConnectorStatus.ACTIVE):
    #     try:
    #         is_healthy = check_connector_health(connector)
    #         if not is_healthy:
    #             connector.status = Connector.ConnectorStatus.ERROR
    #             connector.save()
    #     except Exception as e:
    #         logger.error(f"Error checking status for {connector.type}: {e}")

    return "Connector status update task finished."

from datetime import date, timedelta
from .clients.gsc import GSCClient
from .models import GSCProperty
from content.models import Post
from seo_trends.models import RankTimeSeries

@shared_task
def test_connector_connection(connector_id: str):
    """
    A task to test the connection of a specific connector.
    This is a stub.
    """
    logger.info(f"Testing connection for connector ID: {connector_id}")
    # Simulate a network call
    import time
    time.sleep(2)
    return f"Connection test for {connector_id} completed."

@shared_task
def sync_gsc_property(property_id: str, window_days: int = 7):
    """
    Fetches the latest data from Google Search Console for a given property
    and updates the local database.
    """
    try:
        gsc_property = GSCProperty.objects.get(id=property_id)
        logger.info(f"Starting GSC sync for property: {gsc_property.property_uri}")

        # In a real app, decrypt credentials here
        client = GSCClient(credentials=gsc_property.credentials_encrypted)

        end_date = date.today()
        start_date = end_date - timedelta(days=window_days)

        performance_data = client.get_performance_data(
            property_uri=gsc_property.property_uri,
            start_date=start_date,
            end_date=end_date
        )

        # Process and save the data
        # This is a simplified mapping. A real implementation would be more robust.
        for row in performance_data:
            page_url, query = row['keys']

            # Try to find the corresponding Post
            # This mapping can be complex (e.g., handling URL parameters)
            post = Post.objects.filter(site=gsc_property.site, metadata__url=page_url).first()
            if not post:
                continue

            # Create or update the time series data
            # This assumes one data point per day, but GSC API returns aggregated data.
            # A real implementation needs to handle the date range properly.
            RankTimeSeries.objects.update_or_create(
                post=post,
                query=query,
                date=end_date, # Simplified: use the end date of the sync window
                defaults={
                    'position': row['position'],
                    # Clicks and impressions could be stored in a separate model
                    # or denormalized here if needed.
                }
            )

        gsc_property.last_sync_at = timezone.now()
        gsc_property.save()

        logger.info(f"Successfully synced GSC data for {gsc_property.property_uri}")
        return f"Sync completed for {gsc_property.property_uri}"

    except GSCProperty.DoesNotExist:
        logger.error(f"GSCProperty with ID {property_id} not found.")
    except Exception as e:
        logger.error(f"An error occurred during GSC sync for property {property_id}: {e}")
        # Optionally, re-raise to have Celery retry the task
        raise

@shared_task
def sync_all_gsc_properties():
    """
    Wrapper task that finds all active GSC properties and queues a
    separate sync task for each one.
    """
    active_properties = GSCProperty.objects.filter(site__is_active=True) # Assuming Site has is_active
    logger.info(f"Found {len(active_properties)} GSC properties to sync.")
    for prop in active_properties:
        sync_gsc_property.delay(str(prop.id))
    return f"Queued sync tasks for {len(active_properties)} properties."
