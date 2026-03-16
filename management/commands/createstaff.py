from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from market.models import Staff


class Command(BaseCommand):
    help = 'Create a staff account from the command line'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Staff username')
        parser.add_argument('password', type=str, help='Staff password')
        parser.add_argument('--email', type=str, default='', help='Staff email (optional)')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options.get('email', '') or f'{username}@unimarket.staff'

        if Staff.objects.filter(username=username).exists():
            self.stderr.write(self.style.ERROR(f'Staff "{username}" already exists.'))
            return

        Staff.objects.create(
            username=username,
            email=email,
            password=make_password(password),
        )
        self.stdout.write(self.style.SUCCESS(f'Staff account "{username}" created successfully.'))
