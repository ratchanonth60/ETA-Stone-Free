TENANT_MODEL = "tenants.Client"
TENANT_DOMAIN_MODEL = "tenants.Domain"
DATABASE_ROUTERS = ("ecommerce.core.tenants.routers.TenantSyncRouter",)
PUBLIC_SCHEMA_URLCONF = "eta.urls_public"
TENANT_SYNC_ROUTER = "ecommerce.core.tenants.routers.TenantSyncRouter"
