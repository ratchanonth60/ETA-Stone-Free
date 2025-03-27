from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import cached_property
from django_tenants import utils
from storages.backends.s3boto3 import S3Boto3Storage


class TenantS3Storage(S3Boto3Storage):
    """
    Implementation that extends S3Boto3Storage for multi-tenant setups.
    Files are stored in S3 with a tenant-specific prefix derived from the schema name.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the S3 storage with tenant-specific configuration.
        """
        # Validate required AWS settings
        required_settings = [
            "AWS_STORAGE_BUCKET_NAME",
            "AWS_REGION_NAME",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ]
        for setting in required_settings:
            if not hasattr(settings, setting):
                raise ImproperlyConfigured(f"Missing required setting: {setting}")

        # Set AWS configuration from settings
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.region_name = settings.AWS_REGION_NAME
        self.access_key = settings.AWS_ACCESS_KEY_ID
        self.secret_key = settings.AWS_SECRET_ACCESS_KEY
        self.file_overwrite = getattr(settings, "AWS_S3_FILE_OVERWRITE", False)
        self.default_acl = getattr(settings, "AWS_DEFAULT_ACL", "public-read")

        super().__init__(*args, **kwargs)

    def _clear_cached_properties(self, setting, **kwargs):
        """Reset setting-based property values."""
        super()._clear_cached_properties(setting, **kwargs)
        if setting == "MULTITENANT_RELATIVE_MEDIA_ROOT":
            self.__dict__.pop("relative_media_root", None)

    @cached_property
    def relative_media_root(self):
        """
        Get the base prefix for tenant-specific storage in S3.
        Falls back to empty string if MULTITENANT_RELATIVE_MEDIA_ROOT is not set.
        """
        return getattr(settings, "MULTITENANT_RELATIVE_MEDIA_ROOT", "")

    @cached_property
    def relative_media_url(self):
        """
        Get the base URL prefix for tenant-specific files.
        Uses MULTITENANT_RELATIVE_MEDIA_ROOT if set, otherwise just the tenant schema.
        """
        try:
            multitenant_relative_url = settings.MULTITENANT_RELATIVE_MEDIA_ROOT
        except AttributeError:
            multitenant_relative_url = "%s"  # Will be replaced by tenant schema

        # Ensure proper URL formatting
        base_url = settings.MEDIA_URL if hasattr(settings, "MEDIA_URL") else ""
        multitenant_relative_url = (
            "/".join(s.strip("/") for s in [base_url, multitenant_relative_url]) + "/"
        )
        if not multitenant_relative_url.startswith("/"):
            multitenant_relative_url = "/" + multitenant_relative_url
        return multitenant_relative_url

    @property
    def base_location(self):
        """
        Get the tenant-specific prefix for S3 storage.
        Uses django-tenants' parse_tenant_config_path to inject tenant schema.
        """
        return utils.parse_tenant_config_path(self.relative_media_root).strip("/")

    @property
    def location(self):
        """
        Get the full S3 prefix including tenant information.
        """
        return self.base_location

    def _normalize_name(self, name):
        """
        Prepend the tenant-specific location to the filename.

        Args:
            name (str): Original filename

        Returns:
            str: Normalized path with tenant prefix (e.g., 'tenant1/uploads/file.jpg')
        """
        clean_name = name.lstrip("/")
        return f"{self.location}/{clean_name}" if self.location else clean_name

    @property
    def base_url(self):
        """
        Get the full base URL with tenant-specific prefix.
        """
        relative_tenant_media_url = utils.parse_tenant_config_path(
            self.relative_media_url
        )

        if self._base_url is None:
            return relative_tenant_media_url

        # Combine base_url with tenant-specific path
        relative_tenant_media_url = (
            "/".join(s.strip("/") for s in [self._base_url, relative_tenant_media_url])
            + "/"
        )
        return relative_tenant_media_url

    def listdir(self, path):
        """
        List objects in S3 under the tenant-specific prefix.
        Returns empty lists if prefix doesn't exist (similar to TenantFileSystemStorage).

        Args:
            path (str): Path relative to tenant prefix

        Returns:
            tuple: (dirs, files)
        """
        try:
            full_path = self._normalize_name(path)
            return super().listdir(full_path)
        except Exception:  # S3 might raise various exceptions for missing prefixes
            return [], []  # Mimic TenantFileSystemStorage's forgiving behavior
