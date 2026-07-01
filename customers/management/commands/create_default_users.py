"""
Management command to create default users for the event system.

Usage:
    python manage.py create_default_users

Creates:
    admin  / admin123  (is_staff=True,  is_superuser=True)
    staff  / staff123  (is_staff=False, is_superuser=False)
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create default admin and entry-staff users'

    def handle(self, *args, **options):
        users = [
            {
                'username': 'admin',
                'password': 'admin123',
                'is_staff': True,
                'is_superuser': True,
                'label': 'Admin (full access)',
            },
            {
                'username': 'staff',
                'password': 'staff123',
                'is_staff': False,
                'is_superuser': False,
                'label': 'Entry Staff (register only)',
            },
        ]

        for u in users:
            if User.objects.filter(username=u['username']).exists():
                self.stdout.write(
                    self.style.WARNING(f"  ⚠  User '{u['username']}' already exists — skipped.")
                )
            else:
                User.objects.create_user(
                    username=u['username'],
                    password=u['password'],
                    is_staff=u['is_staff'],
                    is_superuser=u['is_superuser'],
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓  Created {u['label']}: "
                        f"username='{u['username']}' password='{u['password']}'"
                    )
                )

        self.stdout.write(self.style.SUCCESS('\nDone! Change passwords before going live.'))
