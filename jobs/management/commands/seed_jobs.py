import json
from pathlib import Path

from django.core.management.base import BaseCommand

from jobs.models import Job


class Command(BaseCommand):
    help = "Add the initial fictional job listings when the database is empty."

    def handle(self, *args, **options):
        if Job.objects.exists():
            self.stdout.write("Listings already exist; leaving admin changes untouched.")
            return

        fixture = Path(__file__).resolve().parents[2] / "fixtures" / "jobs.json"
        records = json.loads(fixture.read_text(encoding="utf-8"))
        Job.objects.bulk_create(Job(**record) for record in records)
        self.stdout.write(self.style.SUCCESS(f"Added {len(records)} fictional job listings."))
