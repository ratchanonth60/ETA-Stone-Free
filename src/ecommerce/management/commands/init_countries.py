import pycountry
from django.core.management.base import BaseCommand

from ecommerce.apps.address.models import Country


class Command(BaseCommand):
    help = "Populates the list of countries with data from pycountry."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-shipping",
            action="store_false",
            dest="is_shipping",
            default=True,
            help="Don't mark countries for shipping",
        )
        parser.add_argument(
            "--initial-only",
            action="store_true",
            dest="is_initial_only",
            default=False,
            help="Exit quietly without doing anything if countries were already populated.",
        )

    def handle(self, *args, **options):
        # Check if the data already exists in the database
        if Country.objects.exists():
            self.stdout.write(self.style.SUCCESS('Countries data already exists. No changes were made.'))
            return

        countries = [
            Country(
                iso_3166_1_a2=country.alpha_2,
                iso_3166_1_a3=country.alpha_3,
                iso_3166_1_numeric=country.numeric,
                printable_name=country.name,
                name=getattr(country, "official_name", ""),
                # is_shipping_country=options["is_shipping"],
            )
            for country in pycountry.countries
        ]

        # Use bulk_create to insert the data efficiently
        Country.objects.bulk_create(countries)

        self.stdout.write(self.style.SUCCESS('Successfully initialized countries data.'))
