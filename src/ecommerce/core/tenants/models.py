from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Client(TenantMixin):
    name = models.CharField(max_length=100)
    paid_until = models.DateField(auto_now_add=True)
    on_trial = models.BooleanField(default=False)
    created_on = models.DateField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

    def __str__(self):
        return f"{self.name} - {self.schema_name}"


class Domain(DomainMixin):
    def __str__(self):
        return self.domain
