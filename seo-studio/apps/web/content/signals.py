# content/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify as django_slugify
from .models import Post, PostSlugHistory, Redirect301
from textutils import slugify_persian

# A simple approximation for word count and read time
def calculate_read_time(text: str) -> int:
    """Calculates the estimated read time in minutes for a given text."""
    word_count = len(text.split())
    # Assuming an average reading speed of 180 words per minute for Persian
    read_time = word_count / 180
    return max(1, round(read_time)) # Return at least 1 minute

@receiver(pre_save, sender=Post)
def handle_post_pre_save(sender, instance: Post, **kwargs):
    """
    Automations that run before a Post instance is saved.
    - Generates a slug if one isn't provided.
    - Calculates read time.
    - Handles slug changes and creates redirects.
    """
    # 1. Generate slug automatically if not set
    if not instance.slug:
        source = instance.title_en if instance.title_en else instance.title
        instance.slug = slugify_persian(source, allow_unicode=True)

    # 2. (Re)calculate read time based on body_text
    if instance.body_text:
        instance.read_time_min = calculate_read_time(instance.body_text)

    # 3. Handle slug changes to create redirects
    if instance.pk: # If the instance is not new
        try:
            old_instance = Post.objects.get(pk=instance.pk)
            if old_instance.slug != instance.slug and old_instance.slug:
                # Slug has changed, log it and create a redirect
                PostSlugHistory.objects.create(post=instance, old_slug=old_instance.slug)

                # Create a 301 redirect. Assuming a simple /{slug}/ structure.
                # A more robust solution would use reverse() or a site setting.
                from_path = f"/{old_instance.slug}/"
                to_path = f"/{instance.slug}/"

                Redirect301.objects.update_or_create(
                    site=instance.site,
                    from_path=from_path,
                    defaults={'to_path': to_path, 'reason': Redirect301.RedirectReason.SLUG_CHANGE}
                )
        except Post.DoesNotExist:
            pass # Object is new, so no old instance to compare.

@receiver(post_save, sender=Post)
def handle_post_post_save(sender, instance: Post, created: bool, **kwargs):
    """
    Automations that run after a Post instance is saved.
    - Placeholder for post-publication tasks like sending notifications
      or triggering external workflows.
    """
    if instance.status == Post.PostStatus.PUBLISHED:
        # e.g., trigger a task to check for orphan links
        pass
