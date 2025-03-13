# -*- coding: utf-8 -*-
from django.forms.models import inlineformset_factory
from oscar.core.loading import get_classes

from .models import Line, WishList, WishListSharedEmail

WishListLineForm, WishListSharedEmailForm = get_classes(
    "wishlists.forms", ("WishListLineForm", "WishListSharedEmailForm")
)


LineFormset = inlineformset_factory(
    WishList,
    Line,
    fields=("quantity",),
    form=WishListLineForm,
    extra=0,
    can_delete=False,
)
WishListSharedEmailFormset = inlineformset_factory(
    WishList,
    WishListSharedEmail,
    fields=("email",),
    form=WishListSharedEmailForm,
    extra=3,
    can_delete=True,
)
