import contextlib
import logging
from urllib.parse import quote

import stripe
from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views import generic
from oscar.apps.address.forms import UserAddressForm

from ecommerce.apps.address.models import Country, UserAddress
from ecommerce.apps.checkout.exceptions import FailedPreCondition
from ecommerce.apps.checkout.forms import (
    GatewayForm,
    ShippingAddressForm,
    ShippingMethodForm,
)
from ecommerce.apps.checkout.mixins import OrderPlacementMixin
from ecommerce.apps.checkout.session import CheckoutSessionMixin
from ecommerce.apps.order.exceptions import UnableToPlaceOrder
from ecommerce.apps.order.models import Order, PaymentEventType
from ecommerce.apps.payment.exceptions import (
    PaymentError,
    RedirectRequired,
    TransactionDeclined,
    UnableToTakePayment,
)
from ecommerce.apps.payment.forms import BankcardForm, PaymentMethodForm
from ecommerce.apps.payment.models import Bankcard, Source, SourceType
from ecommerce.apps.shipping.methods import NoShippingRequired
from ecommerce.apps.shipping.repository import Repository
from ecommerce.core import signals
from ecommerce.core.celery.tasks.order import send_confirmation_message

# Standard logger for checkout events
logger = logging.getLogger("ecommerce.checkout")


class IndexView(CheckoutSessionMixin, generic.FormView):
    """
    First page of the checkout.  We prompt user to either sign in, or
    to proceed as a guest (where we still collect their email address).
    """

    template_name = "eta/checkout/gateway.html"
    form_class = GatewayForm
    success_url = reverse_lazy("checkout:shipping-address")
    pre_conditions = ["check_basket_is_not_empty", "check_basket_is_valid"]

    def get(self, request, *args, **kwargs):
        # We redirect immediately to shipping address stage if the user is
        # signed in.
        if request.user.is_authenticated:
            # We raise a signal to indicate that the user has entered the
            # checkout process so analytics tools can track this event.
            signals.start_checkout.send_robust(sender=self, request=request)
            return self.get_success_response()
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if email := self.checkout_session.get_guest_email():
            kwargs["initial"] = {
                "username": email,
            }
        return kwargs

    def form_valid(self, form):
        if form.is_guest_checkout():
            self._handle_guest_checkout(form)
        elif form.is_new_account_checkout():
            self._handle_new_account_checkout(form)
        else:
            user = form.get_user()
            login(self.request, user)

            # We raise a signal to indicate that the user has entered the
            # checkout process.
            signals.start_checkout.send_robust(sender=self, request=self.request)

        return redirect(self.get_success_url())

    def _handle_guest_checkout(self, form):
        email = form.cleaned_data["username"]
        self.checkout_session.set_guest_email(email)

        # We raise a signal to indicate that the user has entered the
        # checkout process by specifying an email address.
        signals.start_checkout.send_robust(
            sender=self, request=self.request, email=email
        )

        if form.is_new_account_checkout():
            messages.info(
                self.request,
                _(
                    "Create your account and then you will be redirected "
                    "back to the checkout process"
                ),
            )
            url = f'{reverse("customer:register")}?next={reverse("checkout:shipping-address")}&email={quote(email)}'
            self.success_url = url

    def _handle_new_account_checkout(self, form):
        self._handle_guest_checkout(form)

    def get_success_response(self):
        return redirect(self.get_success_url())


class CheckCountryPreCondition(object):
    """DRY class for check country in session pre_condition"""

    def get_pre_conditions(self, request):
        if "check_country_in_session" not in self.pre_conditions:
            return self.pre_conditions + ["check_country_in_session"]
        return super().get_pre_conditions(request)

    def check_country_in_session(self, request):
        if request.session.get("country", None) is None:
            raise FailedPreCondition(
                url=reverse("checkout:shipping-address"),
            )


# ================
# SHIPPING ADDRESS
# ================


class ShippingAddressView(CheckoutSessionMixin, generic.FormView):
    """
    Determine the shipping address for the order.

    The default behaviour is to display a list of addresses from the users's
    address book, from which the user can choose one to be their shipping
    address.  They can add/edit/delete these USER addresses.  This address will
    be automatically converted into a SHIPPING address when the user checks
    out.

    Alternatively, the user can enter a SHIPPING address directly which will be
    saved in the session and later saved as ShippingAddress model when the
    order is successfully submitted.
    """

    template_name = "eta/checkout/shipping_address.html"
    form_class = ShippingAddressForm
    success_url = reverse_lazy("checkout:shipping-method")
    pre_conditions = [
        "check_basket_is_not_empty",
        "check_basket_is_valid",
        "check_user_email_is_captured",
    ]
    skip_conditions = ["skip_unless_basket_requires_shipping"]

    def get_initial(self):
        initial = self.checkout_session.new_shipping_address_fields()
        if initial:
            initial = initial.copy()
            # Convert the primary key stored in the session into a Country
            # instance
            with contextlib.suppress(Country.DoesNotExist):
                initial["country"] = Country.objects.get(
                    iso_3166_1_a2=initial.pop("country_id")
                )
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # Look up address book data
            ctx["addresses"] = self.get_available_addresses()
        return ctx

    def get_available_addresses(self):
        # Include only addresses where the country is flagged as valid for
        # shipping. Also, use ordering to ensure the default address comes
        # first.
        return self.request.user.addresses.filter(
            country__is_shipping_country=True
        ).order_by("-is_default_for_shipping")

    def post(self, request, *args, **kwargs):
        if (
            not self.request.user.is_authenticated
            or "address_id" not in self.request.POST
        ):
            return super().post(request, *args, **kwargs)
        address = UserAddress._default_manager.get(
            pk=self.request.POST["address_id"], user=self.request.user
        )
        action = self.request.POST.get("action", None)
        if action == "ship_to":
            # User has selected a previous address to ship to
            self.checkout_session.ship_to_user_address(address)
            return redirect(self.get_success_url())
        else:
            return http.HttpResponseBadRequest()

    def form_valid(self, form):
        # Store the address details in the session and redirect to next step
        address_fields = {
            k: v for (k, v) in form.instance.__dict__.items() if not k.startswith("_")
        }
        self.checkout_session.ship_to_new_address(address_fields)
        return super().form_valid(form)


class UserAddressUpdateView(CheckoutSessionMixin, generic.UpdateView):
    """
    Update a user address
    """

    template_name = "eta/checkout/user_address_form.html"
    form_class = UserAddressForm
    success_url = reverse_lazy("checkout:shipping-address")

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        messages.info(self.request, _("Address saved"))
        return super().get_success_url()


class UserAddressDeleteView(CheckoutSessionMixin, generic.DeleteView):
    """
    Delete an address from a user's address book.
    """

    template_name = "eta/checkout/user_address_delete.html"
    success_url = reverse_lazy("checkout:shipping-address")

    def get_queryset(self):
        return self.request.user.addresses.all()

    def get_success_url(self):
        messages.info(self.request, _("Address deleted"))
        return super().get_success_url()


# ===============
# Shipping method
# ===============


class ShippingMethodView(CheckoutSessionMixin, generic.FormView):
    """
    View for allowing a user to choose a shipping method.

    Shipping methods are largely domain-specific and so this view
    will commonly need to be subclassed and customised.

    The default behaviour is to load all the available shipping methods
    using the shipping Repository.  If there is only 1, then it is
    automatically selected.  Otherwise, a page is rendered where
    the user can choose the appropriate one.
    """

    template_name = "eta/checkout/shipping_methods.html"
    form_class = ShippingMethodForm
    pre_conditions = [
        "check_basket_is_not_empty",
        "check_basket_is_valid",
        "check_user_email_is_captured",
    ]
    success_url = reverse_lazy("checkout:payment-method")

    def post(self, request, *args, **kwargs):
        self._methods = self.get_available_shipping_methods()
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # These skip and pre conditions can't easily be factored out into the
        # normal pre-conditions as they do more than run a test and then raise
        # an exception on failure.

        # Check that shipping is required at all
        if not request.basket.is_shipping_required():
            # No shipping required - we store a special code to indicate so.
            self.checkout_session.use_shipping_method(NoShippingRequired().code)
            return self.get_success_response()

        # Check that shipping address has been completed
        if not self.checkout_session.is_shipping_address_set():
            messages.error(request, _("Please choose a shipping address"))
            return redirect("checkout:shipping-address")

        # Save shipping methods as instance var as we need them both here
        # and when setting the context vars.
        self._methods = self.get_available_shipping_methods()
        if len(self._methods) == 0:
            # No shipping methods available for given address
            messages.warning(
                request,
                _(
                    "Shipping is unavailable for your chosen address - please "
                    "choose another"
                ),
            )
            return redirect("checkout:shipping-address")
        elif len(self._methods) == 1:
            # Only one shipping method - set this and redirect onto the next
            # step
            self.checkout_session.use_shipping_method(self._methods[0].code)
            return self.get_success_response()

        # Must be more than one available shipping method, we present them to
        # the user to make a choice.
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["methods"] = self._methods
        return kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["methods"] = self._methods
        return kwargs

    def get_available_shipping_methods(self):
        """
        Returns all applicable shipping method objects for a given basket.
        """
        # Shipping methods can depend on the user, the contents of the basket
        # and the shipping address (so we pass all these things to the
        # repository).  I haven't come across a scenario that doesn't fit this
        # system.
        return Repository().get_shipping_methods(
            basket=self.request.basket,
            user=self.request.user,
            shipping_addr=self.get_shipping_address(self.request.basket),
            request=self.request,
        )

    def form_invalid(self, form):
        messages.error(
            self.request, _("Your submitted shipping method is not permitted")
        )
        return super().form_invalid(form)


# ==============
# Payment method
# ==============


class PaymentMethodView(CheckoutSessionMixin, generic.FormView):
    """
    View for a user to choose which payment method(s) they want to use.

    This would include setting allocations if payment is to be split
    between multiple sources. It's not the place for entering sensitive details
    like bankcard numbers though - that belongs on the payment details view.
    """

    template_name = "eta/checkout/payment_method.html"
    pre_conditions = [
        "check_basket_is_not_empty",
        "check_basket_is_valid",
        "check_user_email_is_captured",
        "check_shipping_data_is_captured",
    ]
    form_class = PaymentMethodForm
    skip_conditions = ["skip_unless_payment_is_required"]
    success_url = reverse_lazy("checkout:payment-details")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        if len(settings.OSCAR_PAYMENT_METHODS) != 1:
            return generic.FormView.get(self, request, *args, **kwargs)
        self.checkout_session.pay_by(settings.OSCAR_PAYMENT_METHODS[0][0])
        return redirect(self.get_success_url())

    def get_initial(self):
        initial_data = super().get_initial()

        # Check if user has a saved card
        if self.request.user.bankcards.exists():
            initial_data["payment_option"] = "saved_card"
            initial_data["has_saved_card"] = True
        return initial_data

    def form_valid(self, form):
        selected_option = form.cleaned_data["payment_option"]

        # Check if selected_option is empty
        if not selected_option:
            form.add_error(
                "payment_option", ValidationError("Please select a payment option.")
            )
            return self.form_invalid(form)  # Render the form back with the error

        if selected_option.isdigit():
            try:
                card = self.request.user.bankcards.get(id=selected_option)
                self.checkout_session.pay_by_saved_card(card.id)
                self.checkout_session.pay_by(card.card_type)
                return redirect(reverse_lazy("checkout:preview"))
            except Exception as e:
                # Handle errors when trying to fetch the card details
                form.add_error("payment_option", str(e))
                return self.form_invalid(form)

        else:
            self.checkout_session.pay_by(selected_option)

        return super().form_valid(form)


class PaymentDetailsView(OrderPlacementMixin, generic.FormView):
    template_name = "eta/checkout/payment_details.html"
    template_name_preview = "eta/checkout/preview.html"
    form_class = BankcardForm
    success_url = reverse_lazy("checkout:preview")
    # These conditions are extended at runtime depending on whether we are in
    # 'preview' mode or not.
    pre_conditions = [
        "check_basket_is_not_empty",
        "check_basket_is_valid",
        "check_user_email_is_captured",
        "check_shipping_data_is_captured",
    ]

    # If preview=True, then we render a preview template that shows all order
    # details ready for submission.
    preview = False

    def get_pre_conditions(self, request):
        if self.preview:
            # The preview view needs to ensure payment information has been
            # correctly captured.
            return self.pre_conditions + ["check_payment_data_is_captured"]
        return super().get_pre_conditions(request)

    def get_skip_conditions(self, request):
        if not self.preview:
            # Payment details should only be collected if necessary
            return ["skip_unless_payment_is_required"]
        return super().get_skip_conditions(request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        payment_session = self.request.session.get("checkout_data").get("payment")
        if payment_session is not None:
            card = self.request.user.bankcards.get(id=payment_session["saved_card_id"])
            ctx["payment"] = card.__str__()
            # if ctx['payment']['method'] == 'blankcard':
            #     ctx['payment']['form'] = {
            #         'blank_card_form': BankcardForm()
            #     }
            # elif get_payment_method_display(ctx["payment_method"]) == 'paypal':
            #     pass
        return ctx

    def post(self, request, *args, **kwargs):
        # Posting to payment-details isn't the right thing to do.  Form
        # submissions should use the preview URL.
        # if not self.preview:
        #     return http.HttpResponseBadRequest()

        # We use a custom parameter to indicate if this is an attempt to place
        # an order (normally from the preview page).  Without this, we assume a
        # payment form is being submitted from the payment details view. In
        # this case, the form needs validating and the order preview shown.
        if request.POST.get("action", "") == "place_order":
            return self.handle_place_order_submission(request)
        return self.handle_payment_details_submission(request)

    def handle_place_order_submission(self, request):
        """
        Handle a request to place an order.

        This method is normally called after the customer has clicked "place
        order" on the preview page. It's responsible for (re-)validating any
        form information then building the submission dict to pass to the
        `submit` method.

        If forms are submitted on your payment details view, you should
        override this method to ensure they are valid before extracting their
        data into the submission dict and passing it onto `submit`.
        """
        return self.submit(**self.build_submission())

    def handle_payment_details_submission(self, request):
        """
        Handle a request to submit payment details.

        This method will need to be overridden by projects that require forms
        to be submitted on the payment details view.  The new version of this
        method should validate the submitted form data and:

        - If the form data is valid, show the preview view with the forms
          re-rendered in the page
        - If the form data is invalid, show the payment details view with
          the form errors showing.

        """
        # No form data to validate by default, so we simply render the preview
        # page.  If validating form data and it's invalid, then call the
        # render_payment_details view.
        return self.render_preview(request)

    def render_preview(self, request, **kwargs):
        """
        Show a preview of the order.

        If sensitive data was submitted on the payment details page, you will
        need to pass it back to the view here so it can be stored in hidden
        form inputs.  This avoids ever writing the sensitive data to disk.
        """
        self.preview = True
        ctx = self.get_context_data(**kwargs)
        return self.render_to_response(ctx)

    def render_payment_details(self, request, **kwargs):
        """
        Show the payment details page

        This method is useful if the submission from the payment details view
        is invalid and needs to be re-rendered with form errors showing.
        """
        self.preview = False
        ctx = self.get_context_data(**kwargs)
        return self.render_to_response(ctx)

    def get_default_billing_address(self):
        """
        Return default billing address for user

        This is useful when the payment details view includes a billing address
        form - you can use this helper method to prepopulate the form.

        Note, this isn't used in core oscar as there is no billing address form
        by default.
        """
        if not self.request.user.is_authenticated:
            return None
        try:
            return self.request.user.addresses.get(is_default_for_billing=True)
        except UserAddress.DoesNotExist:
            return None

    def handle_payment(self, order_number, total, blank_card, **kwargs):
        try:
            with transaction.atomic():
                # Create a payment intent
                source_type = SourceType.objects.get_or_create(
                    name="card"
                )  # type source card

                intent = stripe.PaymentIntent.create(
                    amount=int(total.incl_tax) * 100,  # Stripe accepts amounts in cents
                    currency=total.currency.lower(),
                    payment_method_types=["card"],
                    customer=blank_card.stripe_customer_id,
                    metadata={"order_number": order_number},
                    **kwargs,
                )
                source = Source(
                    source_type=source_type[0],
                    currency=total.currency,
                    amount_allocated=int(total.incl_tax),
                    reference=intent.id,
                    label=order_number,
                )
                # Add payment source (if available)
                self.add_payment_source(source=source)

                # Record payment event
                event_type, _ = PaymentEventType.objects.get_or_create(name="Paid")
                self.add_payment_event(event_type, total.incl_tax, reference=intent.id)
        except stripe.error.CardError as e:
            # Handle declined card error
            raise UnableToTakePayment(e.user_message) from e
        except stripe.error.StripeError as e:
            # Handle general Stripe error
            raise PaymentError(str(e)) from e
        except Exception as e:
            logger.info(f"Order #%s: transaction payment intent fail as {e}", order_number)
            raise TransactionDeclined(str(e)) from e
        return intent

    def send_order_placed_email(self, order):
        send_confirmation_message.delay(order.number)

    def handle_successful_order(self, order):
        """
        Handle the various steps required after an order has been successfully
        placed.

        Override this view if you want to perform custom actions when an
        order is submitted.
        """
        # Send confirmation message (normally an email)
        self.send_order_placed_email(order)

        # Flush all session data
        self.checkout_session.flush()

        # Save order id in session so thank-you page can load it
        self.request.session["checkout_order_id"] = order.id

        response = HttpResponseRedirect(self.get_success_url())
        self.send_signal(self.request, response, order)
        return response

    def handle_order_placement(
        self,
        order_number,
        user,
        basket,
        shipping_address,
        shipping_method,
        shipping_charge,
        billing_address,
        order_total,
        surcharges=None,
        intent=None,
        blank_card=None,
        **kwargs,
    ):
        try:
            with transaction.atomic():
                order = self.place_order(
                    order_number=order_number,
                    user=user,
                    basket=basket,
                    shipping_address=shipping_address,
                    shipping_method=shipping_method,
                    shipping_charge=shipping_charge,
                    order_total=order_total,
                    billing_address=billing_address,
                    surcharges=surcharges,
                    **kwargs,
                )
                basket.submit()
            # Confirm the payment intent
            stripe.PaymentIntent.confirm(
                intent.id,
                payment_method=blank_card.stripe_card_id,
            )
        except stripe.error.CardError as e:
            # Handle declined card error
            raise UnableToTakePayment(e.user_message) from e
        except stripe.error.StripeError as e:
            # Handle general Stripe error
            raise PaymentError(str(e)) from e
        except Exception as e:
            logger.info(f"Order #%s: transaction order fail as {e}", order_number)
            raise TransactionDeclined(str(e)) from e
        return self.handle_successful_order(order)

    def submit(
        self,
        user,
        basket,
        shipping_address,
        shipping_method,  # noqa (too complex (10))
        shipping_charge,
        billing_address,
        order_total,
        payment_kwargs=None,
        order_kwargs=None,
        surcharges=None,
    ):
        """
        Submit a basket for order placement.

        The process runs as follows:

         * Generate an order number
         * Freeze the basket so it cannot be modified any more (important when
           redirecting the user to another site for payment as it prevents the
           basket being manipulated during the payment process).
         * Attempt to take payment for the order
           - If payment is successful, place the order
           - If a redirect is required (e.g. PayPal, 3D Secure), redirect
           - If payment is unsuccessful, show an appropriate error message

        :basket: The basket to submit.
        :payment_kwargs: Additional kwargs to pass to the handle_payment
                         method. It normally makes sense to pass form
                         instances (rather than model instances) so that the
                         forms can be re-rendered correctly if payment fails.
        :order_kwargs: Additional kwargs to pass to the place_order method
        """
        if payment_kwargs is None:
            payment_kwargs = {}
        if order_kwargs is None:
            order_kwargs = {}

        blank_card = Bankcard.objects.get(user__id=user.id)

        # Taxes must be known at this point
        assert (
            basket.is_tax_known
        ), "Basket tax must be set before a user can place an order"
        assert (
            shipping_charge.is_tax_known
        ), "Shipping charge tax must be set before a user can place an order"

        # We generate the order number first as this will be used
        # in payment requests (ie before the order model has been
        # created).  We also save it in the session for multi-stage
        # checkouts (e.g. where we redirect to a 3rd party site and place
        # the order on a different request).
        order_number = self.generate_order_number(basket)
        self.checkout_session.set_order_number(order_number)
        logger.info(
            "Order #%s: beginning submission process for basket #%d",
            order_number,
            basket.id,
        )

        # Freeze the basket so it cannot be manipulated while the customer is
        # completing payment on a 3rd party site.  Also, store a reference to
        # the basket in the session so that we know which basket to thaw if we
        # get an unsuccessful payment response when redirecting to a 3rd party
        # site.
        self.freeze_basket(basket)
        self.checkout_session.set_submitted_basket(basket)

        # We define a general error message for when an unanticipated payment
        # error occurs.
        error_msg = _(
            "A problem occurred while processing payment for this "
            "order - no payment has been taken.  Please "
            "contact customer services if this problem persists"
        )

        signals.pre_payment.send_robust(sender=self, view=self)

        try:
            intent = self.handle_payment(
                order_number, order_total, blank_card, **payment_kwargs
            )
        except RedirectRequired as e:
            # Redirect required (e.g. PayPal, 3DS)
            logger.info("Order #%s: redirecting to %s", order_number, e.url)
            return http.HttpResponseRedirect(e.url)
        except UnableToTakePayment as e:
            # Something went wrong with payment but in an anticipated way.  Eg
            # their bankcard has expired, wrong card number - that kind of
            # thing. This type of exception is supposed to set a friendly error
            # message that makes sense to the customer.
            msg = str(e)
            logger.warning(
                "Order #%s: unable to take payment (%s) - restoring basket",
                order_number,
                msg,
            )
            self.restore_frozen_basket()

            # We assume that the details submitted on the payment details view
            # were invalid (e.g. expired bankcard).
            return self.render_payment_details(
                self.request, error=msg, **payment_kwargs
            )
        except PaymentError as e:
            # A general payment error - Something went wrong which wasn't
            # anticipated.  Eg, the payment gateway is down (it happens), your
            # credentials are wrong - that king of thing.
            # It makes sense to configure the checkout logger to
            # mail admins on an error as this issue warrants some further
            # investigation.
            msg = str(e)
            logger.error(
                "Order #%s: payment error (%s)", order_number, msg, exc_info=True
            )
            self.restore_frozen_basket()
            return self.render_preview(self.request, error=error_msg, **payment_kwargs)
        except Exception as e:
            # Unhandled exception - hopefully, you will only ever see this in
            # development...
            logger.exception(
                "Order #%s: unhandled exception while taking payment (%s)",
                order_number,
                e,
            )
            self.restore_frozen_basket()
            return self.render_preview(self.request, error=error_msg, **payment_kwargs)

        signals.post_payment.send_robust(sender=self, view=self)

        # If all is ok with payment, try and place order
        logger.info("Order #%s: payment successful, placing order", order_number)
        try:
            return self.handle_order_placement(
                order_number,
                user,
                basket,
                shipping_address,
                shipping_method,
                shipping_charge,
                billing_address,
                order_total,
                surcharges=surcharges,
                intent=intent,
                blank_card=blank_card,
                **order_kwargs,
            )
        except UnableToPlaceOrder as e:
            # It's possible that something will go wrong while trying to
            # actually place an order.  Not a good situation to be in as a
            # payment transaction may already have taken place, but needs
            # to be handled gracefully.
            msg = str(e)
            logger.error(
                "Order #%s: unable to place order - %s",
                order_number,
                msg,
                exc_info=True,
            )
            self.restore_frozen_basket()
            return self.render_preview(self.request, error=msg, **payment_kwargs)
        except Exception as e:
            # Hopefully you only ever reach this in development
            logger.exception(
                "Order #%s: unhandled exception while placing order (%s)",
                order_number,
                e,
            )
            error_msg = _(
                "A problem occurred while placing this order. Please contact customer services."
            )
            self.restore_frozen_basket()
            return self.render_preview(self.request, error=error_msg, **payment_kwargs)

    def get_template_names(self):
        return [self.template_name_preview] if self.preview else [self.template_name]


# =========
# Thank you
# =========


class ThankYouView(generic.DetailView):
    """
    Displays the 'thank you' page which summarises the order just submitted.
    """

    template_name = "eta/checkout/thank_you.html"
    context_object_name = "order"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            return redirect(settings.OSCAR_HOMEPAGE)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        # We allow superusers to force an order thank-you page for testing
        order = None
        if self.request.user.is_superuser:
            kwargs = {}
            if "order_number" in self.request.GET:
                kwargs["number"] = self.request.GET["order_number"]
            elif "order_id" in self.request.GET:
                kwargs["id"] = self.request.GET["order_id"]
            order = Order._default_manager.filter(**kwargs).first()

        if not order and "checkout_order_id" in self.request.session:
            order = Order._default_manager.filter(
                pk=self.request.session["checkout_order_id"]
            ).first()
        return order

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        # Remember whether this view has been loaded.
        # Only send tracking information on the first load.
        key = f'order_{ctx["order"].pk}_thankyou_viewed'
        session = not self.request.session.get(key, False)
        if session:
            self.request.session[key] = session
        ctx["send_analytics_event"] = session
        return ctx
