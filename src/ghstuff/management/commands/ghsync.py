
from django.core.management.base import BaseCommand

from ghstuff import sync_gh_data


class Command(BaseCommand):
    help = "Download all Github data to local DB (might take several hours)."

    def add_arguments(self, parser):
        parser.add_argument('--organization', required=True)
        parser.add_argument('--repository', action='append')
        parser.add_argument('--type', action='append')

    def handle(self, *args, **options):
        org = options['organization']
        repos = options['repository']
        types = options['type']
        self.stdout.write('Importing Github data from organization "%s"' % org)
        sync_gh_data(org, repos, types)
        self.stdout.write(self.style.SUCCESS('Done. All Good!'))
