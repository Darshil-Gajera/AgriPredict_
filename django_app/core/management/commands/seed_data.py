"""
Management command: seed_data
Loads all fixtures in the correct order.

Usage:
    python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Load all initial fixture data (colleges, scholarships)"

    def handle(self, *args, **kwargs):
        self.stdout.write("Loading college fixtures...")
        call_command("loaddata", "colleges/fixtures/colleges.json")
        self.stdout.write(self.style.SUCCESS("✓ Colleges loaded"))

        self.stdout.write("Loading scholarship fixtures...")
        call_command("loaddata", "scholarships/fixtures/scholarships.json")
        self.stdout.write(self.style.SUCCESS("✓ Scholarships loaded"))

        self.stdout.write(self.style.SUCCESS("\n✅ All seed data loaded successfully!"))
        self.stdout.write("\nNext steps:")
        self.stdout.write("  python manage.py createsuperuser")
        self.stdout.write("  python manage.py runserver")
