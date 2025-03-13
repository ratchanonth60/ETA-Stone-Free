from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from .models import Client, Domain


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("tenant", "domain", "is_primary")
    search_fields = ("tenant__name", "domain")


class DomainInline(admin.TabularInline):
    model = Domain
    list_display = (
        "tenant",
        "domain",
        "is_primary",
    )


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "schema_name",
        "get_primary_domain",
        "created_on",
    )
    search_fields = ("name", "schema_name")
    inlines = (DomainInline,)

    def get_primary_domain(self, obj):
        return obj.get_primary_domain()

    get_primary_domain.short_description = "Primary Domain"
