
import os
import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ["DJANGO_SUPERUSER_USERNAME"]
email = os.environ["DJANGO_SUPERUSER_EMAIL"]
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]

if User.objects.filter(username=username).exists():
    print("Administrator username already exists.", flush=True)
else:
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
    )
    print("Administrator created successfully.", flush=True)
