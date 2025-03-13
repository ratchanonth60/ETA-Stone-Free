# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from oscar.apps.wishlists.abstract_models import (
    AbstractLine,
    AbstractWishList,
    AbstractWishListSharedEmail,
)
from oscar.core.compat import AUTH_USER_MODEL


class WishList(AbstractWishList):
    # Only authenticated users can have wishlists
    owner = models.ForeignKey(
        AUTH_USER_MODEL,
        related_name="wishlists",
        on_delete=models.CASCADE,
        verbose_name=_("Owner"),
    )
    name = models.CharField(
        verbose_name=_("Name"), default=_("Default"), max_length=255
    )

    #: This key acts as primary key and is used instead of an int to make it
    #: harder to guess
    key = models.CharField(
        _("Key"), max_length=6, db_index=True, unique=True, editable=False
    )

    # Oscar core does not support public or shared wishlists at the moment, but
    # all the right hooks should be there
    PUBLIC, PRIVATE, SHARED = ("Public", "Private", "Shared")
    VISIBILITY_CHOICES = (
        (PRIVATE, _("Private - Only the owner can see the wish list")),
        (
            SHARED,
            _(
                "Shared - Only the owner and people with access to the"
                " obfuscated link can see the wish list"
            ),
        ),
        (PUBLIC, _("Public - Everybody can see the wish list")),
    )
    visibility = models.CharField(
        _("Visibility"), max_length=20, default=PRIVATE, choices=VISIBILITY_CHOICES
    )

    # Convention: A user can have multiple wish lists. The last created wish
    # list for a user shall be their "default" wish list.
    # If an UI element only allows adding to wish list without
    # specifying which one , one shall use the default one.
    # That is a rare enough case to handle it by convention instead of a
    # BooleanField.
    date_created = models.DateTimeField(
        _("Date created"), auto_now_add=True, editable=False, db_index=True
    )


class Line(AbstractLine):
    wishlist = models.ForeignKey(
        "wishlists.WishList",
        on_delete=models.CASCADE,
        related_name="lines",
        verbose_name=_("Wish List"),
    )
    product = models.ForeignKey(
        "catalogue.Product",
        verbose_name=_("Product"),
        related_name="wishlists_lines",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    quantity = models.PositiveIntegerField(_("Quantity"), default=1)
    #: Store the title in case product gets deleted
    title = models.CharField(pgettext_lazy("Product title", "Title"), max_length=255)


class WishListSharedEmail(AbstractWishListSharedEmail):
    wishlist = models.ForeignKey(
        "wishlists.WishList",
        on_delete=models.CASCADE,
        related_name="shared_emails",
        verbose_name=_("Wish List"),
    )
    email = models.EmailField(verbose_name=_("Email"))
