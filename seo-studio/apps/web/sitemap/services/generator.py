# sitemap/services/generator.py
import gzip
import logging
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
from typing import List, Dict, Any

from core.models import Site
from content.models import Post
from ..models import SitemapRule, HreflangMap, SitemapBuildLog

logger = logging.getLogger(__name__)

# Configurable settings
SITEMAP_MAX_URLS = 50000
SITEMAP_BASE_PATH = 'sitemaps'

class SitemapGenerator:
    def __init__(self, site: Site):
        self.site = site
        self.log = None
        self.urls = []
        self.sitemap_files = []

    def _get_posts(self):
        """Fetches all published posts for the site."""
        return Post.objects.filter(site=self.site, status=Post.PostStatus.PUBLISHED).order_by('-published_at')

    def _get_rule_for_post(self, post: Post, rules: List[SitemapRule]) -> SitemapRule:
        """Finds the most specific sitemap rule for a given post."""
        # This can be optimized, but is fine for a moderate number of rules.
        for rule in rules:
            if rule.post_type == post.type:
                return rule
        for rule in rules:
            if rule.post_type == '*':
                return rule
        return None

    def _normalize_priority(self, post: Post) -> float:
        """Normalizes priority based on role, freshness, etc. Placeholder logic."""
        # Simple logic: newer posts get slightly higher priority.
        days_since_published = (timezone.now() - post.published_at).days
        freshness_boost = max(0, 0.1 - (days_since_published / 3650)) # Small boost for posts in last year

        # In a real app, you would also factor in clicks, rank, etc.
        base_priority = 0.5 # Default

        return min(1.0, base_priority + freshness_boost)


    def _build_url_list(self):
        """Builds the list of URL dictionaries for the sitemap."""
        posts = self._get_posts()
        rules = list(SitemapRule.objects.filter(site=self.site, is_active=True))

        for post in posts:
            rule = self._get_rule_for_post(post, rules)
            priority = self._normalize_priority(post)
            changefreq = 'weekly' # Default

            if rule:
                priority = rule.priority
                changefreq = rule.changefreq

            # Hreflang alternates
            hreflang_map = HreflangMap.objects.filter(source_url=post.full_url).first()
            alternates = hreflang_map.alternates if hreflang_map else []

            self.urls.append({
                'loc': post.full_url,
                'lastmod': post.updated_at.isoformat(),
                'changefreq': changefreq,
                'priority': priority,
                'alternates': alternates
            })

    def _write_sitemap_file(self, file_index: int, urls: List[Dict]):
        """Renders and writes a single sitemap XML file."""
        file_path = f"{SITEMAP_BASE_PATH}/{self.site.id}/sitemap-{file_index}.xml.gz"

        xml_content = render_to_string('sitemap/sitemap.xml', {'urlset': urls})
        gzipped_content = gzip.compress(xml_content.encode('utf-8'))

        if default_storage.exists(file_path):
            default_storage.delete(file_path)

        default_storage.save(file_path, ContentFile(gzipped_content))
        self.sitemap_files.append(default_storage.url(file_path))


    def _write_sitemap_index(self):
        """Renders and writes the sitemap index file."""
        index_path = f"{SITEMAP_BASE_PATH}/{self.site.id}/sitemap.xml"

        xml_content = render_to_string('sitemap/sitemap_index.xml', {
            'sitemaps': self.sitemap_files,
            'lastmod': datetime.now().isoformat(),
        })

        if default_storage.exists(index_path):
            default_storage.delete(index_path)

        default_storage.save(index_path, ContentFile(xml_content.encode('utf-8')))

    def generate(self):
        """The main method to generate the sitemap(s)."""
        self.log = SitemapBuildLog.objects.create(site=self.site, status=SitemapBuildLog.Status.STARTED)

        try:
            self._build_url_list()

            # Split URLs into chunks and write sitemap files
            for i in range(0, len(self.urls), SITEMAP_MAX_URLS):
                chunk = self.urls[i:i + SITEMAP_MAX_URLS]
                self._write_sitemap_file(i // SITEMAP_MAX_URLS + 1, chunk)

            self._write_sitemap_index()

            self.log.status = SitemapBuildLog.Status.COMPLETED
            self.log.url_count = len(self.urls)
            self.log.file_count = len(self.sitemap_files)

        except Exception as e:
            logger.error(f"Sitemap generation failed for site {self.site.id}: {e}")
            self.log.status = SitemapBuildLog.Status.FAILED
            self.log.errors = str(e)

        self.log.save()

def generate_sitemap_for_site(site_id: str):
    try:
        site = Site.objects.get(id=site_id)
        generator = SitemapGenerator(site)
        generator.generate()
    except Site.DoesNotExist:
        logger.error(f"Cannot generate sitemap: Site with ID {site_id} not found.")
