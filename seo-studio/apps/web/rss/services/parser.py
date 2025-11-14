# rss/services/parser.py
import feedparser
import requests
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime
from django.utils import timezone

from ..models import FeedSource, FeedItem, FeedRunLog

class FeedParser:
    def __init__(self, source: FeedSource):
        self.source = source
        self.log = None

    def _fetch_feed(self):
        """Fetches the raw feed content with a timeout and user-agent."""
        headers = {'User-Agent': 'SEOStudioBot/1.0'}
        response = requests.get(self.source.url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.content

    def _parse_entry(self, entry) -> dict:
        """Parses a single feed entry into a standardized dictionary."""
        published_time = timezone.make_aware(datetime(*entry.published_parsed[:6])) if hasattr(entry, 'published_parsed') else timezone.now()

        # Create a stable unique identifier
        guid = entry.get('id') or entry.get('link') or entry.title
        guid_hash = hashlib.sha256(guid.encode('utf-8')).hexdigest()

        return {
            'guid_hash': guid_hash,
            'title': entry.get('title', ''),
            'url': entry.get('link', ''),
            'published_at': published_time,
            'author': entry.get('author', ''),
            'summary_raw': entry.get('summary', ''),
            'content_raw': entry.get('content', [{}])[0].get('value', ''),
        }

    def _clean_html(self, html: str) -> str:
        """Removes boilerplate and sanitizes HTML. Placeholder logic."""
        # In a real app, use a library like 'trafilatura' or 'goose3'
        soup = BeautifulSoup(html, 'html.parser')
        # Simple example: remove all script and style tags
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        return str(soup.body)

    def process(self):
        """Main method to fetch, parse, and store feed items."""
        self.log = FeedRunLog.objects.create(source=self.source, started_at=timezone.now())

        try:
            raw_content = self._fetch_feed()
            feed = feedparser.parse(raw_content)

            self.log.fetched = len(feed.entries)
            new_items_count = 0

            for entry in feed.entries:
                parsed_data = self._parse_entry(entry)

                item, created = FeedItem.objects.get_or_create(
                    guid_hash=parsed_data['guid_hash'],
                    defaults={
                        'source': self.source,
                        **parsed_data
                    }
                )
                if created:
                    new_items_count += 1

            self.log.new = new_items_count
            self.source.last_checked_at = timezone.now()
            self.source.last_error = ""

        except Exception as e:
            self.source.last_error = str(e)
            self.log.errors = [{"error": str(e)}]

        finally:
            self.log.finished_at = timezone.now()
            self.log.save()
            self.source.save()

def check_feed_source(source_id: str):
    try:
        source = FeedSource.objects.get(id=source_id)
        parser = FeedParser(source)
        parser.process()
    except FeedSource.DoesNotExist:
        logging.error(f"FeedSource with ID {source_id} not found.")
