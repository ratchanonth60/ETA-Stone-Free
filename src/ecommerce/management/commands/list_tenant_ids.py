from django.core.management.base import BaseCommand

from ecommerce.core.tenants.models import Domain


class Command(BaseCommand):
    help = "List all tenant IDs and their domains"

    def add_arguments(self, parser):
        parser.add_argument(
            "--domains", action="store_true", help="Include domain names"
        )

    def handle(self, *args, **options):
        include_domains = options["domains"]
        domains = []
        for domain in Domain.objects.all():
            if include_domains:
                # Assuming Client model has a domain_set related name for Domain model
                domains.append(domain.domain)
                self.stdout.write(f"{domain.id}: {', '.join(domains)}")
            else:
                self.stdout.write(str(domain.id))
