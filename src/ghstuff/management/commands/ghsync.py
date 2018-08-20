
from django.core.management.base import BaseCommand

from ghstuff import sync_gh_data


class Command(BaseCommand):
    help = "Download all Github data to local DB (might take several hours)."

    def add_arguments(self, parser):
        parser.add_argument('--organization', required=True)

    def handle(self, *args, **options):
        org = options['organization']
        self.stdout.write('Importing Github data from organization "%s"' % org)
        sync_gh_data(org)
        self.stdout.write(self.style.SUCCESS('Done. All Good!'))
