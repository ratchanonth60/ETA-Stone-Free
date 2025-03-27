from django.core.management.base import BaseCommand
from django.db import connection

from ecommerce.apps.users.models import User
from ecommerce.core.tenants.models import Client


class Command(BaseCommand):
    help = "Create a user in a specific tenant schema with a password"

    def add_arguments(self, parser):
        parser.add_argument("schema_name", type=str, help="Schema name of the tenant")
        parser.add_argument("username", type=str, help="Username for the new user")
        parser.add_argument("email", type=str, help="Email for the new user")
        parser.add_argument("password", type=str, help="Password for the new user")
        parser.add_argument(
            "--superuser", action="store_true", help="Make the user a superuser"
        )

    def handle(self, *args, **options):
        schema_name = options["schema_name"]
        username = options["username"]
        email = options["email"]
        password = options["password"]
        is_superuser = options["superuser"]

        try:
            client = Client.objects.get(schema_name=schema_name)
            connection.set_tenant(client)
        except Client.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant '{schema_name}' not found"))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"User '{username}' already exists in '{schema_name}'"
                )
            )
            return

        if is_superuser:
            User.objects.create_superuser(
                username=username, email=email, password=password
            )
        else:
            User.objects.create_user(username=username, email=email, password=password)

        self.stdout.write(
            self.style.SUCCESS(f"User '{username}' created in '{schema_name}'")
        )
