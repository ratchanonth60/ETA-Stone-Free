import pytest
from django.conf import settings


@pytest.fixture(scope="session")
def django_db_setup():
    settings.DATABASES["default"]["NAME"] = "test_eta"
    settings.DATABASES["default"]["TEST"] = {"NAME": "test_eta", "CREATE_DB": False}
