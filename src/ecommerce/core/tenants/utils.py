from django_tenants.utils import get_public_schema_name


class IsPublicSchema(object):
    @staticmethod
    def is_public_schema_request(request):
        return (
            not hasattr(request, "tenant")
            or request.tenant.schema_name == get_public_schema_name()
        )
