import logging

import stripe
from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic
from oscar.apps.address.forms import UserAddressForm
from oscar.apps.customer import signals
from oscar.apps.customer.utils import get_password_reset_url
from oscar.core.loading import get_profile_class
from oscar.core.utils import safe_referrer
from oscar.views.generic import PostActionMixin

from ecommerce.apps.address.models import UserAddress
from ecommerce.apps.communication.models import Email
from ecommerce.apps.customer.forms import (
    ConfirmPasswordForm,
    EmailAuthenticationForm,
    EmailUserCreationForm,
    OrderSearchForm,
    ProfileForm,
)
from ecommerce.apps.customer.mixins import PageTitleMixin, RegisterUserMixin
from ecommerce.apps.customer.utils import CustomerDispatcher
from ecommerce.apps.order.models import Order
from ecommerce.apps.payment.forms import BankcardForm
from ecommerce.apps.payment.models import Bankcard
from ecommerce.apps.users.models import User
from ecommerce.core.celery.tasks.email import send_registration_email_for_user

logger = logging.getLogger(__name__)
# =======
# Account
# =======


class AccountSummaryView(generic.RedirectView):
    """
    View that exists for legacy reasons and customisability. It commonly gets
    called when the user clicks on "Account" in the navbar.

    Oscar defaults to just redirecting to the profile summary page (and
    that redirect can be configured via OSCAR_ACCOUNT_REDIRECT_URL), but
    it's also likely you want to display an 'account overview' page or
    such like. The presence of this view allows just that, without
    having to change a lot of templates.
    """

    pattern_name = settings.OSCAR_ACCOUNTS_REDIRECT_URL
    permanent = False


class AccountRegistrationView(RegisterUserMixin, generic.FormView):
    form_class = EmailUserCreationForm
    template_name = "eta/customer/registration.html"
    redirect_field_name = "next"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().get(request, *args, **kwargs)

    def get_logged_in_redirect(self):
        return reverse("customer:summary")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = {
            "email": self.request.GET.get("email", ""),
            "redirect_url": self.request.GET.get(self.redirect_field_name, ""),
        }
        kwargs["host"] = self.request.get_host()
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["cancel_url"] = safe_referrer(self.request, "")
        return ctx

    def form_valid(self, form):
        self.register_user(form)
        return redirect(form.cleaned_data["redirect_url"])


class AccountAuthView(RegisterUserMixin, generic.TemplateView):
    """
    This is actually a slightly odd double form view that allows a customer to
    either login or register.
    """

    template_name = "eta/customer/login_registration.html"
    login_prefix, registration_prefix = "login", "registration"
    login_form_class = EmailAuthenticationForm
    registration_form_class = EmailUserCreationForm
    redirect_field_name = "next"

    def send_registration_email(self, user):
        send_registration_email_for_user.delay(user.pk)

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        if "login_form" not in kwargs:
            ctx["login_form"] = self.get_login_form()
        if "registration_form" not in kwargs:
            ctx["registration_form"] = self.get_registration_form()
        return ctx

    def post(self, request, *args, **kwargs):
        # Use the name of the submit button to determine which form to validate
        if "login_submit" in request.POST:
            return self.validate_login_form()
        elif "registration_submit" in request.POST:
            return self.validate_registration_form()
        return http.HttpResponseBadRequest()

    # LOGIN

    def get_login_form(self, bind_data=False):
        return self.login_form_class(**self.get_login_form_kwargs(bind_data))

    def get_login_form_kwargs(self, bind_data=False):
        kwargs = {"request": self.request, "host": self.request.get_host()}
        kwargs["prefix"] = self.login_prefix
        kwargs["initial"] = {
            "redirect_url": self.request.GET.get(self.redirect_field_name, ""),
        }
        if bind_data and self.request.method in ("POST", "PUT"):
            kwargs |= {
                "data": self.request.POST,
                "files": self.request.FILES,
            }
        return kwargs

    def validate_login_form(self):
        form = self.get_login_form(bind_data=True)
        if form.is_valid():
            return self._login_successful(form)
        ctx = self.get_context_data(login_form=form)
        return self.render_to_response(ctx)

    def _login_successful(self, form):
        user = form.get_user()

        # Grab a reference to the session ID before logging in
        old_session_key = self.request.session.session_key

        auth_login(self.request, form.get_user())

        # Raise signal robustly (we don't want exceptions to crash the
        # request handling). We use a custom signal as we want to track the
        # session key before calling login (which cycles the session ID).
        signals.user_logged_in.send_robust(
            sender=self,
            request=self.request,
            user=user,
            old_session_key=old_session_key,
        )

        if msg := self.get_login_success_message(form):
            messages.success(self.request, msg)

        return redirect(self.get_login_success_url(form))

    def get_login_success_message(self, form):
        return _("Welcome back")

    def get_login_success_url(self, form):
        if redirect_url := form.cleaned_data["redirect_url"]:
            return redirect_url

        # Redirect staff members to dashboard as that's the most likely place
        # they'll want to visit if they're logging in.
        if self.request.user.is_staff:
            return reverse("dashboard:index")

        return settings.LOGIN_REDIRECT_URL

    # REGISTRATION

    def get_registration_form(self, bind_data=False):
        return self.registration_form_class(
            **self.get_registration_form_kwargs(bind_data)
        )

    def get_registration_form_kwargs(self, bind_data=False):
        kwargs = {"host": self.request.get_host()}
        kwargs["prefix"] = self.registration_prefix
        kwargs["initial"] = {
            "redirect_url": self.request.GET.get(self.redirect_field_name, ""),
        }
        if bind_data and self.request.method in ("POST", "PUT"):
            kwargs |= {
                "data": self.request.POST,
                "files": self.request.FILES,
            }
        return kwargs

    def validate_registration_form(self):
        form = self.get_registration_form(bind_data=True)
        if form.is_valid():
            self.register_user(form)

            msg = self.get_registration_success_message(form)
            messages.success(self.request, msg)

            return redirect(self.get_registration_success_url(form))

        ctx = self.get_context_data(registration_form=form)
        return self.render_to_response(ctx)

    def get_registration_success_message(self, form):
        return _("Thanks for registering!")

    def get_registration_success_url(self, form):
        if redirect_url := form.cleaned_data["redirect_url"]:
            return redirect_url

        return settings.LOGIN_REDIRECT_URL


class LogoutView(generic.RedirectView):
    url = settings.OSCAR_HOMEPAGE
    permanent = False

    def get(self, request, *args, **kwargs):
        auth_logout(request)
        response = super().get(request, *args, **kwargs)

        for cookie in settings.OSCAR_COOKIES_DELETE_ON_LOGOUT:
            response.delete_cookie(cookie)

        return response


# =============
# Profile
# =============


class ProfileView(PageTitleMixin, generic.TemplateView):
    template_name = "eta/customer/profile/profile.html"
    page_title = _("Profile")
    active_tab = "profile"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["profile_fields"] = self.get_profile_fields(self.request.user)
        return ctx

    def get_profile_fields(self, user):
        field_data = [
            self.get_model_field_data(user, field_name)
            for field_name in User._meta.additional_fields
        ]
        if profile_class := get_profile_class():
            try:
                profile = profile_class.objects.get(user=user)
            except ObjectDoesNotExist:
                profile = profile_class(user=user)

            field_names = [f.name for f in profile._meta.local_fields]
            field_data.extend(
                self.get_model_field_data(profile, field_name)
                for field_name in field_names
                if field_name not in ("user", "id")
            )
        return field_data

    def get_model_field_data(self, model_class, field_name):
        """
        Extract the verbose name and value for a model's field value
        """
        field = model_class._meta.get_field(field_name)
        if field.choices:
            value = getattr(model_class, f"get_{field_name}_display")()
        else:
            value = getattr(model_class, field_name)
        return {
            "name": getattr(field, "verbose_name"),
            "value": value,
        }


class ProfileUpdateView(PageTitleMixin, generic.FormView):
    form_class = ProfileForm
    template_name = "eta/customer/profile/profile_form.html"
    page_title = _("Edit Profile")
    active_tab = "profile"
    success_url = reverse_lazy("customer:profile-view")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Grab current user instance before we save form.  We may need this to
        # send a warning email if the email address is changed.
        try:
            old_user = User.objects.get(id=self.request.user.id)
        except User.DoesNotExist:
            old_user = None

        form.save()

        # We have to look up the email address from the form's
        # cleaned data because the object created by form.save() can
        # either be a user or profile instance depending whether a profile
        # class has been specified by the AUTH_PROFILE_MODULE setting.
        new_email = form.cleaned_data.get("email")
        if new_email and old_user and new_email != old_user.email:
            # Email address has changed - send a confirmation email to the old
            # address including a password reset link in case this is a
            # suspicious change.
            self.send_email_changed_email(old_user, new_email)

        messages.success(self.request, _("Profile updated"))
        return redirect(self.get_success_url())

    def send_email_changed_email(self, old_user, new_email):
        user = self.request.user
        extra_context = {
            "user": user,
            "reset_url": get_password_reset_url(old_user),
            "new_email": new_email,
            "request": self.request,
        }
        CustomerDispatcher().send_email_changed_email_for_user(old_user, extra_context)


class ProfileDeleteView(PageTitleMixin, generic.FormView):
    form_class = ConfirmPasswordForm
    template_name = "eta/customer/profile/profile_delete.html"
    page_title = _("Delete profile")
    active_tab = "profile"
    success_url = settings.OSCAR_HOMEPAGE

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        self.request.user.delete()
        messages.success(
            self.request,
            _("Your profile has now been deleted. Thanks for using the site."),
        )
        return redirect(self.get_success_url())


class ChangePasswordView(PageTitleMixin, generic.FormView):
    form_class = PasswordChangeForm
    template_name = "eta/customer/profile/change_password_form.html"
    page_title = _("Change Password")
    active_tab = "profile"
    success_url = reverse_lazy("customer:profile-view")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, self.request.user)
        messages.success(self.request, _("Password updated"))

        self.send_password_changed_email()

        return redirect(self.get_success_url())

    def send_password_changed_email(self):
        user = self.request.user
        extra_context = {
            "user": user,
            "reset_url": get_password_reset_url(self.request.user),
            "request": self.request,
        }
        CustomerDispatcher().send_password_changed_email_for_user(user, extra_context)


# =============
# Email history
# =============


class EmailHistoryView(PageTitleMixin, generic.ListView):
    context_object_name = "emails"
    template_name = "eta/communication/email/email_list.html"
    paginate_by = settings.OSCAR_EMAILS_PER_PAGE
    page_title = _("Email History")
    active_tab = "emails"

    def get_queryset(self):
        """
        Return Queryset of :py:class:`Email <oscar.apps.customer.abstract_models.AbstractEmail>`
        instances, that has been sent to the currently authenticated user.
        """  # noqa
        return Email._default_manager.filter(user=self.request.user)


class EmailDetailView(PageTitleMixin, generic.DetailView):
    """Customer email"""

    template_name = "eta/communication/email/email_detail.html"
    context_object_name = "email"
    active_tab = "emails"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Email, user=self.request.user, id=self.kwargs["email_id"]
        )

    def get_page_title(self):
        """Append email subject to page title"""
        return f'{_("Email")}: {self.object.subject}'


# =============
# Order history
# =============


class OrderHistoryView(PageTitleMixin, generic.ListView):
    """
    Customer order history
    """

    context_object_name = "orders"
    template_name = "eta/customer/order/order_list.html"
    paginate_by = settings.OSCAR_ORDERS_PER_PAGE
    model = Order
    form_class = OrderSearchForm
    page_title = _("Order History")
    active_tab = "orders"

    def get(self, request, *args, **kwargs):
        if "date_from" in request.GET:
            self.form = self.form_class(self.request.GET)
            if not self.form.is_valid():
                self.object_list = self.get_queryset()
                ctx = self.get_context_data(object_list=self.object_list)
                return self.render_to_response(ctx)
            data = self.form.cleaned_data

            # If the user has just entered an order number, try and look it up
            # and redirect immediately to the order detail page.
            if data["order_number"] and not data["date_to"] and not data["date_from"]:
                try:
                    order = Order.objects.get(
                        number=data["order_number"], user=self.request.user
                    )
                except Order.DoesNotExist:
                    pass
                else:
                    return redirect("customer:order", order_number=order.number)
        else:
            self.form = self.form_class()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return Queryset of :py:class:`Order <oscar.apps.order.abstract_models.AbstractOrder>`
        instances for the currently authenticated user.
        """  # noqa
        qs = self.model._default_manager.filter(user=self.request.user)
        if self.form.is_bound and self.form.is_valid():
            qs = qs.filter(**self.form.get_filters())
        return qs

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx["form"] = self.form
        return ctx


class OrderDetailView(PageTitleMixin, PostActionMixin, generic.DetailView):
    model = Order
    active_tab = "orders"

    def get_template_names(self):
        return ["eta/customer/order/order_detail.html"]

    def get_page_title(self):
        """
        Order number as page title
        """
        return f'{_("Order")} #{self.object.number}'

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model, user=self.request.user, number=self.kwargs["order_number"]
        )

    def do_reorder(self, order):  # noqa (too complex (10))
        """
        'Re-order' a previous order.

        This puts the contents of the previous order into your basket
        """
        # Collect lines to be added to the basket and any warnings for lines
        # that are no longer available.
        basket = self.request.basket
        lines_to_add = []
        warnings = []
        for line in order.lines.all():
            is_available, reason = line.is_available_to_reorder(
                basket, self.request.strategy
            )
            if is_available:
                lines_to_add.append(line)
            else:
                warnings.append(reason)

        # Check whether the number of items in the basket won't exceed the
        # maximum.
        total_quantity = sum(line.quantity for line in lines_to_add)
        is_quantity_allowed, reason = basket.is_quantity_allowed(total_quantity)
        if not is_quantity_allowed:
            messages.warning(self.request, reason)
            self.response = redirect("customer:order-list")
            return

        # Add any warnings
        for warning in warnings:
            messages.warning(self.request, warning)

        for line in lines_to_add:
            options = [
                {"option": attribute.option, "value": attribute.value}
                for attribute in line.attributes.all()
                if attribute.option
            ]
            basket.add_product(line.product, line.quantity, options)

        if lines_to_add:
            self.response = redirect("basket:summary")
            messages.info(
                self.request,
                _(
                    "All available lines from order %(number)s "
                    "have been added to your basket"
                )
                % {"number": order.number},
            )
        else:
            self.response = redirect("customer:order-list")
            messages.warning(
                self.request,
                _(
                    "It is not possible to re-order order %(number)s "
                    "as none of its lines are available to purchase"
                )
                % {"number": order.number},
            )


class OrderLineView(PostActionMixin, generic.DetailView):
    """Customer order line"""

    def get_object(self, queryset=None):
        order = get_object_or_404(
            Order, user=self.request.user, number=self.kwargs["order_number"]
        )
        return order.lines.get(id=self.kwargs["line_id"])

    def do_reorder(self, line):
        self.response = redirect("customer:order", self.kwargs["order_number"])
        basket = self.request.basket

        line_available_to_reorder, reason = line.is_available_to_reorder(
            basket, self.request.strategy
        )

        if not line_available_to_reorder:
            messages.warning(self.request, reason)
            return

        # We need to pass response to the get_or_create... method
        # as a new basket might need to be created
        self.response = redirect("basket:summary")

        options = [
            {"option": attribute.option, "value": attribute.value}
            for attribute in line.attributes.all()
            if attribute.option
        ]
        basket.add_product(line.product, line.quantity, options)

        if line.quantity > 1:
            msg = _(
                "%(qty)d copies of '%(product)s' have been added to your basket"
            ) % {"qty": line.quantity, "product": line.product}
        else:
            msg = _("'%s' has been added to your basket") % line.product

        messages.info(self.request, msg)


class AnonymousOrderDetailView(generic.DetailView):
    model = Order
    template_name = "eta/customer/anon_order.html"

    def get_object(self, queryset=None):
        # Check URL hash matches that for order to prevent spoof attacks
        order = get_object_or_404(
            self.model, user=None, number=self.kwargs["order_number"]
        )
        if not order.check_verification_hash(self.kwargs["hash"]):
            raise http.Http404()
        return order


# ------------
# Address book
# ------------


class AddressListView(PageTitleMixin, generic.ListView):
    """Customer address book"""

    context_object_name = "addresses"
    template_name = "eta/customer/address/address_list.html"
    paginate_by = settings.OSCAR_ADDRESSES_PER_PAGE
    active_tab = "addresses"
    page_title = _("Address Book")

    def get_queryset(self):
        """Return customer's addresses"""
        return UserAddress._default_manager.filter(user=self.request.user)


class AddressCreateView(PageTitleMixin, generic.CreateView):
    form_class = UserAddressForm
    model = UserAddress
    template_name = "eta/customer/address/address_form.html"
    active_tab = "addresses"
    page_title = _("Add a new address")
    success_url = reverse_lazy("customer:address-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Add a new address")
        return ctx

    def get_success_url(self):
        messages.success(self.request, _("Address '%s' created") % self.object.summary)
        return super().get_success_url()


class AddressUpdateView(PageTitleMixin, generic.UpdateView):
    form_class = UserAddressForm
    model = UserAddress
    template_name = "eta/customer/address/address_form.html"
    active_tab = "addresses"
    page_title = _("Edit address")
    success_url = reverse_lazy("customer:address-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Edit address")
        return ctx

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_success_url(self):
        messages.success(self.request, _("Address '%s' updated") % self.object.summary)
        return super().get_success_url()


class AddressDeleteView(PageTitleMixin, generic.DeleteView):
    model = UserAddress
    template_name = "eta/customer/address/address_delete.html"
    page_title = _("Delete address?")
    active_tab = "addresses"
    context_object_name = "address"
    success_url = reverse_lazy("customer:address-list")

    def get_queryset(self):
        return UserAddress._default_manager.filter(user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, _("Address '%s' deleted") % self.object.summary)
        return super().get_success_url()


class AddressChangeStatusView(generic.RedirectView):
    """
    Sets an address as default_for_(billing|shipping)
    """

    url = reverse_lazy("customer:address-list")
    permanent = False

    def get(self, request, pk=None, action=None, *args, **kwargs):
        address = get_object_or_404(UserAddress, user=self.request.user, pk=pk)
        #  We don't want the user to set an address as the default shipping
        #  address, though they should be able to set it as their billing
        #  address.
        if address.country.is_shipping_country:
            setattr(address, f"is_{action}", True)
        elif action == "default_for_billing":
            setattr(address, "is_default_for_billing", True)
        else:
            messages.error(request, _("We do not ship to this country"))
        address.save()
        return super().get(request, *args, **kwargs)


# ------------
# Payment Management
# ------------
class PaymentManagementListView(LoginRequiredMixin, PageTitleMixin, generic.ListView):
    context_object_name = "payments"
    login_url = reverse_lazy("customer:login")
    template_name = "eta/customer/payment/payment_management_list.html"
    active_tab = "payment"
    page_title = _("Payment Management")

    def get_queryset(self):
        """Return blank cards"""
        return Bankcard._default_manager.filter(user=self.request.user)


class PaymentManagementCreateView(
    LoginRequiredMixin, PageTitleMixin, generic.CreateView
):
    form_class = BankcardForm
    model = Bankcard
    login_url = reverse_lazy("customer:login")
    template_name = "eta/customer/payment/payment_management_form.html"
    active_tab = "payment"
    page_title = _("Add a payment card")
    success_url = reverse_lazy("customer:payment-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Add a payment card")
        return ctx

    def form_valid(self, form):
        # Use Stripe's library to create a new charge
        token = form.cleaned_data["stripeToken"]

        # Here you can create a Customer or direct Charge on Stripe based on your requirement
        try:
            customer = stripe.Customer.create(
                name=self.request.user.username,
                email=self.request.user.email,
                source=token,
            )
            bankcard = form.save(commit=False)
            bankcard.stripe_customer_id = customer.id
            bankcard.stripe_card_id = customer.default_source
            bankcard.save()

            # Now call the method to update other details
            bankcard.update_card_details_from_stripe()
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        messages.success(
            self.request, _("Payment '%s' created") % self.object.stripe_customer_id
        )
        return super().get_success_url()
