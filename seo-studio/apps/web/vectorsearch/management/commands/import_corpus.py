# vectorsearch/management/commands/import_corpus.py
import csv
from django.core.management.base import BaseCommand, CommandError
from core.models import Site
from vectorsearch.models import Corpus
from vectorsearch.services.ingest import ingest_document

class Command(BaseCommand):
    help = 'Imports documents from a CSV file into a specified corpus.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='Path to the CSV file to import.')
        parser.add_argument('--site-id', type=str, required=True, help='The ID of the site this corpus belongs to.')
        parser.add_argument('--corpus-name', type=str, required=True, help='The name of the corpus to create or use.')

    def handle(self, *args, **options):
        file_path = options['file']
        site_id = options['site_id']
        corpus_name = options['corpus_name']

        try:
            site = Site.objects.get(id=site_id)
        except Site.DoesNotExist:
            raise CommandError(f"Site with ID '{site_id}' does not exist.")

        corpus, created = Corpus.objects.get_or_create(
            site=site,
            name=corpus_name,
            defaults={'source': Corpus.Source.IMPORT}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Successfully created new corpus: '{corpus_name}'"))
        else:
            self.stdout.write(f"Using existing corpus: '{corpus_name}'")

        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                # Expects columns: external_id, title, raw_text, url, tags (comma-separated)
                for row in reader:
                    self.stdout.write(f"Ingesting document with external_id: {row['external_id']}...")
                    ingest_document(
                        corpus_id=str(corpus.id),
                        external_id=row['external_id'],
                        title=row['title'],
                        raw_text=row['raw_text'],
                        metadata={
                            'url': row.get('url'),
                            'tags': [tag.strip() for tag in row.get('tags', '').split(',')],
                        }
                    )
            self.stdout.write(self.style.SUCCESS("Successfully queued all documents for ingestion."))
        except FileNotFoundError:
            raise CommandError(f"File not found at: {file_path}")
        except Exception as e:
            raise CommandError(f"An error occurred during import: {e}")
