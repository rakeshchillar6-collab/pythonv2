# core/management/commands/seed.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Organization, Site
from content.models import Category, Post

class Command(BaseCommand):
    help = 'Seeds the database with initial data for development.'

    def handle(self, *args, **options):
        self.stdout.write('Starting database seeding...')

        # Clean up existing data to avoid conflicts
        Post.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Site.objects.all().delete()
        Organization.objects.all().delete()

        self.stdout.write('Existing data cleared.')

        # Create a superuser if it doesn't exist
        if not User.objects.filter(email='admin@example.com').exists():
            admin_user = User.objects.create_superuser(
                email='admin@example.com',
                password='adminpassword'
            )
            self.stdout.write(self.style.SUCCESS('Superuser created.'))
        else:
            admin_user = User.objects.get(email='admin@example.com')

        # Create an editor user
        editor_user, created = User.objects.get_or_create(
            email='editor@example.com',
            defaults={'first_name': 'Editor', 'last_name': 'User'}
        )
        if created:
            editor_user.set_password('editorpassword')
            editor_user.save()
            self.stdout.write(self.style.SUCCESS('Editor user created.'))

        # Create Organization and Site
        org = Organization.objects.create(name='My Company', owner=admin_user)
        org.members.add(editor_user)
        Site.objects.create(organization=org, name='Main Blog', domain='example.com')
        self.stdout.write(self.style.SUCCESS('Organization and Site created.'))

        # Create Categories
        cat_tech = Category.objects.create(name='Technology', slug='technology')
        cat_health = Category.objects.create(name='Health', slug='health')
        cat_business = Category.objects.create(name='Business', slug='business')
        self.stdout.write(self.style.SUCCESS('Categories created.'))

        # Create Posts
        Post.objects.create(
            title='The Future of AI',
            slug='future-of-ai',
            content='<p>The future of AI is bright and full of possibilities...</p>',
            excerpt='A look into the future of Artificial Intelligence.',
            status=Post.PostStatus.PUBLISHED,
            published_at=timezone.now(),
            author=editor_user,
            category=cat_tech
        )
        Post.objects.create(
            title='10 Tips for a Healthier Lifestyle',
            slug='healthier-lifestyle-tips',
            content='<p>Living a healthier life is easier than you think. Here are 10 tips...</p>',
            excerpt='Simple and effective tips for improving your health.',
            status=Post.PostStatus.PUBLISHED,
            published_at=timezone.now(),
            author=editor_user,
            category=cat_health
        )
        Post.objects.create(
            title='Understanding Blockchain',
            slug='understanding-blockchain',
            content='<p>Blockchain is a decentralized ledger technology...</p>',
            excerpt='A beginner\'s guide to blockchain technology.',
            status=Post.PostStatus.DRAFT,
            author=admin_user,
            category=cat_tech
        )
        self.stdout.write(self.style.SUCCESS('Sample posts created.'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
