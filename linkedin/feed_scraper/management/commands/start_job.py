from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'starts the cron job'

    def handle(self, *args, **options):
        self.stdout.write('sup big boi')
