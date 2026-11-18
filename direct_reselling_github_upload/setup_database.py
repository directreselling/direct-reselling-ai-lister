
import os
import django
from django.core.management import call_command

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)
django.setup()

print("Starting database migrations...", flush=True)

call_command("migrate", interactive=False)

print("Database migrations completed successfully.", flush=True)
