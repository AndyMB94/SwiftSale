import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Waits for the database to be available'

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        for attempt in range(30):
            try:
                connection.ensure_connection()
                self.stdout.write(self.style.SUCCESS('Database ready.'))
                return
            except OperationalError:
                self.stdout.write(f'Attempt {attempt + 1}/30 — retrying in 1s...')
                time.sleep(1)
        self.stderr.write(self.style.ERROR('Database unavailable after 30 attempts.'))
        raise SystemExit(1)
