# -*- coding: utf-8 -*-

import re

from django.contrib.auth.models import BaseUserManager
from django.core import validators
from django.db import connection, models
from django.utils.translation import gettext_lazy as _
from django_tenants.utils import get_public_schema_name
from oscar.apps.customer.abstract_models import AbstractUser


class CustomUserManager(BaseUserManager):

    def create_user(self, username, email, password):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=CustomUserManager.normalize_email(email),
            username=username,
            is_active=True,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        u = self.create_user(username, email, password=password)
        u.is_admin = True
        u.is_staff = True
        u.is_superuser = True
        u.save(using=self._db)
        return u


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

    objects = CustomUserManager()
    REQUIRED_FIELDS = ["username"]

    class Meta:
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
