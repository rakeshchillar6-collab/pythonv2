# vectorsearch/management/commands/reembed.py
from django.core.management.base import BaseCommand, CommandError
from vectorsearch.models import Corpus, EmbeddingVersion
from vectorsearch.tasks import reembed_corpus_task

class Command(BaseCommand):
    help = 'Queues a re-embedding task for a specific corpus or all corpora.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--corpus',
            type=str,
            help='The ID of the corpus to re-embed. If not provided, all active corpora will be re-embedded.',
        )
        parser.add_argument(
            '--target-version',
            type=str,
            required=True,
            help='The ID of the target EmbeddingVersion to use for re-embedding.',
        )

    def handle(self, *args, **options):
        corpus_id = options['corpus']
        target_version_id = options['target-version']

        try:
            target_version = EmbeddingVersion.objects.get(id=target_version_id)
            self.stdout.write(f"Targeting embedding version: {target_version}")
        except EmbeddingVersion.DoesNotExist:
            raise CommandError(f"EmbeddingVersion with ID '{target_version_id}' does not exist.")

        corpora_to_reembed = []
        if corpus_id:
            try:
                corpus = Corpus.objects.get(id=corpus_id)
                corpora_to_reembed.append(corpus)
            except Corpus.DoesNotExist:
                raise CommandError(f"Corpus with ID '{corpus_id}' does not exist.")
        else:
            corpora_to_reembed = list(Corpus.objects.filter(is_active=True))
            self.stdout.write(f"Found {len(corpora_to_reembed)} active corpora to re-embed.")

        if not corpora_to_reembed:
            self.stdout.write(self.style.WARNING("No corpora found to re-embed."))
            return

        for corpus in corpora_to_reembed:
            self.stdout.write(f"Queueing re-embedding for corpus '{corpus.name}' ({corpus.id})...")
            reembed_corpus_task.delay(str(corpus.id), str(target_version.id))

        self.stdout.write(self.style.SUCCESS("All re-embedding tasks have been successfully queued."))
