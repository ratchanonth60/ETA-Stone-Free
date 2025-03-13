from django.db import connection
from django.http import HttpResponseBadRequest
from django_tenants.middleware import TenantMainMiddleware as BaseTenantMiddleware
from django_tenants.utils import get_public_schema_name, get_tenant_model


class TenantMainMiddleware(BaseTenantMiddleware):
    """
    Custom middleware to check and set the appropriate tenant.
    """

    def __init__(self, *args, **kwargs):
        super(TenantMainMiddleware, self).__init__(*args, **kwargs)
        self.public_schema_name = get_public_schema_name()

    def get_subdomain(self, request):
        host = request.get_host().split(":")[
            0
        ]  # This will remove the port number if it exists
        domain_parts = host.split(".")
        if len(domain_parts) >= 1:
            list_domain_test = ["tenant", "testserver"]
            return (
                "fast_test" if domain_parts[0] in list_domain_test else domain_parts[0]
            )
        return None

    def hostname_from_request(self, request):
        """Extracts hostname from request. Used for custom tenant selection."""
        # change this if your tenant identification is different e.g. using paths
        return self.get_subdomain(request)

    def get_tenant(self, domain_model, hostname):
        # Check if the hostname is public

        if hostname == self.public_schema_name:
            return domain_model.objects.get(schema_name=self.public_schema_name)

        try:
            return domain_model.objects.get(schema_name=hostname)
        except domain_model.DoesNotExist:
            # If tenant doesn't exist, fallback to public
            return domain_model.objects.get(schema_name=self.public_schema_name)

    def process_request(self, request):
        # Use the tenant associated with the request's domain.
        connection.set_schema_to_public()

        hostname = self.hostname_from_request(request)
        domain_model = get_tenant_model()
        tenant = self.get_tenant(domain_model, hostname)

        if tenant:
            request.tenant = tenant
        else:
            return HttpResponseBadRequest(b"Invalid tenant")

        # Set the current schema to be used for this tenant
        tenant.domain_url = hostname
        request.tenant = tenant
        connection.set_tenant(request.tenant)
        self.setup_url_routing(request)
