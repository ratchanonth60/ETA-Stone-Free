import re

from django.core import validators
from django.db import connection, models
from django.utils.translation import gettext_lazy as _
from django_tenants.utils import get_public_schema_name
from oscar.apps.customer.abstract_models import AbstractUser, UserManager


class User(AbstractUser):
    """
    Custom user based on Oscar's AbstractUser
    """

    username = models.CharField(
        _("username"),
        max_length=30,
        unique=True,
        help_text=_(
            "Required. 30 characters or fewer. Letters, numbers and "
            "@/./+/-/_ characters"
        ),
        validators=[
            validators.RegexValidator(
                re.compile(r"^[\w.@+-]+$"), _("Enter a valid username."), "invalid"
            )
        ],
    )
    extra_field = models.CharField(_("Nobody needs me"), max_length=5, blank=True)
    objects = UserManager()
    REQUIRED_FIELDS = ["username"]
    USERNAME_FIELD = "email"

    class Meta(AbstractUser.Meta):
        app_label = "users"
        ordering = ["-id"]

    def _migrate_alerts_to_user(self):
        """
        Transfer any active alerts linked to a user's email address to the
        newly registered user.
        """
        if connection.get_schema() != get_public_schema_name():
            ProductAlert = self.alerts.model
            alerts = ProductAlert.objects.filter(
                email=self.email, status=ProductAlert.ACTIVE
            )
            alerts.update(user=self, key="", email="")
