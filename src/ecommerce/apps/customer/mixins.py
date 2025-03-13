import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login

from ecommerce.apps.customer.signals import user_registered
from ecommerce.apps.customer.utils import CustomerDispatcher
from ecommerce.apps.users.models import User

logger = logging.getLogger(__name__)


class PageTitleMixin(object):
    """
    Passes page_title and active_tab into context, which makes it quite useful
    for the accounts views.

    Dynamic page titles are possible by overriding get_page_title.
    """

    page_title = None
    active_tab = None

    # Use a method that can be overridden and customised
    def get_page_title(self):
        return self.page_title

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("page_title", self.get_page_title())
        ctx.setdefault("active_tab", self.active_tab)
        return ctx


class RegisterUserMixin(object):

    def register_user(self, form):
        """
        Create a user instance and send a new registration email (if configured
        to).
        """
        user = form.save()

        # Raise signal robustly (we don't want exceptions to crash the request
        # handling).
        user_registered.send_robust(sender=self, request=self.request, user=user)
        if getattr(settings, "OSCAR_SEND_REGISTRATION_EMAIL", True):
            self.send_registration_email(user)

        # We have to authenticate before login
        try:
            user = authenticate(
                username=user.email,
                password=form.cleaned_data["password1"],
            )
            # Check if authentication was successful
            if user is not None:
                # Log in the user
                auth_login(self.request, user)
            else:
                # Handle unsuccessful authentication
                logger.warning("Authentication failed after registration.")
        except User.MultipleObjectsReturned:
            # Handle race condition where the registration request is made
            # multiple times in quick succession.  This leads to both requests
            # passing the uniqueness check and creating users (as the first one
            # hasn't committed when the second one runs the check).  We retain
            # the first one and deactivate the dupes.
            logger.warning(
                "Multiple users with identical email address and password"
                "were found. Marking all but one as not active."
            )
            # As this section explicitly deals with the form being submitted
            # twice, this is about the only place in Oscar where we don't
            # ignore capitalisation when looking up an email address.
            # We might otherwise accidentally mark unrelated users as inactive
            users = User.objects.filter(email=user.email)
            user = users[0]
            for u in users[1:]:
                u.is_active = False
                u.save()

        auth_login(self.request, user)

        return user

    def send_registration_email(self, user):
        extra_context = {"user": user, "request": self.request}
        CustomerDispatcher().send_registration_email_for_user(user, extra_context)
