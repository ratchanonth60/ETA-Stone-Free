import contextlib

from django import shortcuts
from django.contrib import messages
from django.contrib.sessions.serializers import JSONSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, JsonResponse, QueryDict
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, View
from extra_views import ModelFormSetView
from oscar.apps.basket.forms import (
    AddToBasketForm,
    BasketLineForm,
    BasketVoucherForm,
    SavedLineForm,
)
from oscar.apps.basket.formsets import BasketLineFormSet, SavedLineFormSet
from oscar.apps.basket.signals import basket_addition, voucher_addition, voucher_removal
from oscar.apps.checkout.applicator import SurchargeApplicator
from oscar.apps.checkout.calculators import OrderTotalCalculator
from oscar.apps.offer.applicator import Applicator
from oscar.apps.shipping.repository import Repository
from oscar.core import ajax
from oscar.core.utils import is_ajax, redirect_to_referrer, safe_referrer

from ecommerce.apps.basket.models import Basket, Line
from ecommerce.apps.basket.utils import BasketMessageGenerator
from ecommerce.apps.catalogue.models import Product
from ecommerce.apps.voucher.models import Voucher


class BasketView(ModelFormSetView):
    model = Line
    basket_model = Basket
    formset_class = BasketLineFormSet
    form_class = BasketLineForm
    factory_kwargs = {"extra": 0, "can_delete": True}
    template_name = "eta/basket/basket.html"

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs["strategy"] = self.request.strategy
        return kwargs

    def get_queryset(self):
        """
        Return list of :py:class:`Line <oscar.apps.basket.abstract_models.AbstractLine>`
        instances associated with the current basket.
        """  # noqa: E501
        return self.request.basket.all_lines()

    def get_shipping_methods(self, basket):
        return Repository().get_shipping_methods(
            basket=self.request.basket, user=self.request.user, request=self.request
        )

    def get_default_shipping_address(self):
        if self.request.user.is_authenticated:
            return self.request.user.addresses.filter(
                is_default_for_shipping=True
            ).first()

    def get_default_shipping_method(self, basket):
        return Repository().get_default_shipping_method(
            basket=self.request.basket,
            user=self.request.user,
            request=self.request,
            shipping_addr=self.get_default_shipping_address(),
        )

    def get_basket_warnings(self, basket):
        """
        Return a list of warnings that apply to this basket
        """
        warnings = []
        for line in basket.all_lines():
            if warning := line.get_warning():
                warnings.append(warning)
        return warnings

    def get_upsell_messages(self, basket):
        offers = Applicator().get_offers(basket, self.request.user, self.request)
        applied_offers = list(basket.offer_applications.offers.values())
        msgs = []
        for offer in offers:
            if (
                offer.is_condition_partially_satisfied(basket)
                and offer not in applied_offers
            ):
                data = {"message": offer.get_upsell_message(basket), "offer": offer}
                msgs.append(data)
        return msgs

    def get_basket_voucher_form(self):
        """
        This is a separate method so that it's easy to e.g. not return a form
        if there are no vouchers available.
        """
        return BasketVoucherForm()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["voucher_form"] = self.get_basket_voucher_form()

        # Shipping information is included to give an idea of the total order
        # cost.  It is also important for PayPal Express where the customer
        # gets redirected away from the basket page and needs to see what the
        # estimated order total is beforehand.
        context["shipping_methods"] = self.get_shipping_methods(self.request.basket)
        method = self.get_default_shipping_method(self.request.basket)
        context["shipping_method"] = method
        shipping_charge = method.calculate(self.request.basket)
        context["shipping_charge"] = shipping_charge
        if method.is_discounted:
            excl_discount = method.calculate_excl_discount(self.request.basket)
            context["shipping_charge_excl_discount"] = excl_discount
        context["basket_warnings"] = self.get_basket_warnings(self.request.basket)
        context["upsell_messages"] = self.get_upsell_messages(self.request.basket)

        if self.request.user.is_authenticated:
            try:
                saved_basket = self.basket_model.saved.get(owner=self.request.user)
            except self.basket_model.DoesNotExist:
                pass
            else:
                saved_basket.strategy = self.request.basket.strategy
                if not saved_basket.is_empty:
                    saved_queryset = saved_basket.all_lines()
                    formset = SavedLineFormSet(
                        strategy=self.request.strategy,
                        basket=self.request.basket,
                        queryset=saved_queryset,
                        prefix="saved",
                    )
                    context["saved_formset"] = formset

        surcharges = SurchargeApplicator(
            self.request, context
        ).get_applicable_surcharges(
            self.request.basket, shipping_charge=shipping_charge
        )
        context["surcharges"] = surcharges
        context["order_total"] = OrderTotalCalculator().calculate(
            self.request.basket, shipping_charge, surcharges=surcharges
        )
        return context

    def get_success_url(self):
        return safe_referrer(self.request, "basket:summary")

    def formset_valid(self, formset):
        # Store offers before any changes are made so we can inform the user of
        # any changes
        offers_before = self.request.basket.applied_offers()
        save_for_later = False

        # Keep a list of messages - we don't immediately call
        # django.contrib.messages as we may be returning an AJAX response in
        # which case we pass the messages back in a JSON payload.
        flash_messages = ajax.FlashMessages()

        for form in formset:
            if hasattr(form, "cleaned_data") and form.cleaned_data.get(
                "save_for_later", False
            ):
                if self.request.user.is_authenticated:
                    line = form.instance
                    self.move_line_to_saved_basket(line)

                    msg = render_to_string(
                        "eta/basket/messages/line_saved.html", {"line": line}
                    )
                    flash_messages.info(msg)

                    save_for_later = True
                else:
                    msg = _("You can't save an item for later if you're not logged in!")
                    flash_messages.error(msg)
                    return redirect(self.get_success_url())

        if save_for_later:
            # No need to call super if we're moving lines to the saved basket
            response = redirect(self.get_success_url())
        else:
            # Save changes to basket as per normal
            response = super().formset_valid(formset)

        # If AJAX submission, don't redirect but reload the basket content HTML
        if is_ajax(self.request):
            return self._extracted_from_formset_valid_43(offers_before, flash_messages)
        BasketMessageGenerator().apply_messages(self.request, offers_before)

        return response

    # TODO Rename this here and in `formset_valid`
    def _extracted_from_formset_valid_43(self, offers_before, flash_messages):
        # Reload basket and apply offers again
        self.request.basket = Basket.objects.get(id=self.request.basket.id)
        self.request.basket.strategy = self.request.strategy
        Applicator().apply(self.request.basket, self.request.user, self.request)
        offers_after = self.request.basket.applied_offers()

        for level, msg in BasketMessageGenerator().get_messages(
            self.request.basket, offers_before, offers_after, include_buttons=False
        ):
            flash_messages.add_message(level, msg)

        # Reload formset - we have to remove the POST fields from the
        # kwargs as, if they are left in, the formset won't construct
        # correctly as there will be a state mismatch between the
        # management form and the database.
        kwargs = self.get_formset_kwargs()
        del kwargs["data"]
        del kwargs["files"]
        if "queryset" in kwargs:
            del kwargs["queryset"]
        formset = self.get_formset()(queryset=self.get_queryset(), **kwargs)
        ctx = self.get_context_data(formset=formset, basket=self.request.basket)
        return self.json_response(ctx, flash_messages)

    def json_response(self, ctx, flash_messages):
        basket_html = render_to_string(
            "eta/basket/partials/basket_content.html", context=ctx, request=self.request
        )

        return JsonResponse(
            {"content_html": basket_html, "messages": flash_messages.as_dict()}
        )

    def move_line_to_saved_basket(self, line):
        saved_basket, _ = Basket.saved.get_or_create(owner=self.request.user)
        saved_basket.merge_line(line)

    def formset_invalid(self, formset):
        has_deletion = any(formset._should_delete_form(form) for form in formset.forms)
        if has_deletion:
            self.remove_deleted_forms(formset)
            has_no_invalid_non_deletion = all(
                form.is_valid() or formset._should_delete_form(form)
                for form in formset.forms
            )
            if has_no_invalid_non_deletion:
                return self.formset_valid(formset)

        flash_messages = ajax.FlashMessages()
        flash_messages.warning(
            _(
                "Your basket has got some issues. "
                "Please correct any validation errors below."
            )
        )

        if is_ajax(self.request):
            ctx = self.get_context_data(formset=formset, basket=self.request.basket)
            return self.json_response(ctx, flash_messages)

        flash_messages.apply_to_request(self.request)
        return super().formset_invalid(formset)

    def remove_deleted_forms(self, formset):
        """
        Removes forms marked for deletion, from the formset, as well as deletes
        their model instance objects; and modifies the formset's request data,
        to match the state of the data in the database, for the remaining forms.

        This is useful for redisplaying a formset containing other invalid
        forms, after deleting one of the forms from it.
        """
        form_data = {}
        form_index = 0
        for form in formset.forms:
            # Delete forms marked for deletion, and retain the request data
            # for the other forms
            if formset._should_delete_form(form):
                if form.instance.id is not None:
                    form.instance.delete()
            else:
                old_form_prefix = form.prefix
                new_form_prefix = formset.add_prefix(form_index)
                for field_name in form.fields:
                    form.prefix = old_form_prefix
                    old_prefixed_field_name = form.add_prefix(field_name)
                    form.prefix = new_form_prefix
                    new_prefixed_field_name = form.add_prefix(field_name)
                    with contextlib.suppress(KeyError):
                        form_data[new_prefixed_field_name] = formset.data[
                            old_prefixed_field_name
                        ]
                form_index += 1
        for field_name in formset.management_form.fields:
            prefixed_field_name = formset.management_form.add_prefix(field_name)
            if field_name in ["INITIAL_FORMS", "TOTAL_FORMS"]:
                form_data[prefixed_field_name] = str(form_index)
            else:
                form_data[prefixed_field_name] = formset.data[prefixed_field_name]

        query_dict = QueryDict(mutable=True)
        query_dict.update(form_data)
        formset.data = query_dict
        # Clear cached values, so that they are recomputed using the modified
        # request data
        del formset.management_form
        del formset.forms
        # Clean the formset's modified request data
        formset.full_clean()


class BasketAddView(FormView):
    """
    Handles the add-to-basket submissions, which are triggered from various
    parts of the site. The add-to-basket form is loaded into templates using
    a templatetag from :py:mod:`oscar.templatetags.basket_tags`.
    """

    form_class = AddToBasketForm
    product_model = Product
    add_signal = basket_addition
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        self.product = shortcuts.get_object_or_404(self.product_model, pk=kwargs["pk"])
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["basket"] = self.request.basket
        kwargs["product"] = self.product
        return kwargs

    def form_invalid(self, form):
        msgs = [error.as_text() for error in form.errors.values()]
        clean_msgs = [m.replace("* ", "") for m in msgs if m.startswith("* ")]
        messages.error(self.request, ",".join(clean_msgs))

        # We serialize the POST data with JSONSerializer before adding it to the session.
        # Without this, we could expose the site to a security vulnerability
        # if the SESSION_SERIALIZER has been configured to 'django.contrib.sessions.serializers.PickleSerializer'.
        # see: https://docs.djangoproject.com/en/3.2/topics/http/sessions/#cookie-session-backend
        serialized_data = JSONSerializer().dumps(self.request.POST)
        self.request.session[f"add_to_basket_form_post_data_{self.product.pk}"] = (
            serialized_data.decode("latin-1")
        )

        return redirect_to_referrer(self.request, "basket:summary")

    def form_valid(self, form):
        offers_before = self.request.basket.applied_offers()

        self.request.basket.add_product(
            form.product, form.cleaned_data["quantity"], form.cleaned_options()
        )

        messages.success(
            self.request, self.get_success_message(form), extra_tags="safe noicon"
        )

        # Check for additional offer messages
        BasketMessageGenerator().apply_messages(self.request, offers_before)

        # Send signal for basket addition
        self.add_signal.send(
            sender=self,
            product=form.product,
            user=self.request.user,
            request=self.request,
        )

        return super().form_valid(form)

    def get_success_message(self, form):
        return render_to_string(
            "eta/basket/messages/addition.html",
            {"product": form.product, "quantity": form.cleaned_data["quantity"]},
        )

    def get_success_url(self):
        post_url = self.request.POST.get("next")
        if post_url and url_has_allowed_host_and_scheme(
            post_url, self.request.get_host()
        ):
            return post_url
        return safe_referrer(self.request, "basket:summary")


class VoucherAddView(FormView):
    form_class = BasketVoucherForm
    voucher_model = Voucher
    add_signal = voucher_addition

    def get(self, request, *args, **kwargs):
        return redirect("basket:summary")

    def apply_voucher_to_basket(self, voucher):
        if voucher.is_expired():
            messages.error(
                self.request,
                _("The '%(code)s' voucher has expired") % {"code": voucher.code},
            )
            return

        if not voucher.is_active():
            messages.error(
                self.request,
                _("The '%(code)s' voucher is not active") % {"code": voucher.code},
            )
            return

        is_available, message = voucher.is_available_to_user(self.request.user)
        if not is_available:
            messages.error(self.request, message)
            return

        self.request.basket.vouchers.add(voucher)

        # Raise signal
        self.add_signal.send(sender=self, basket=self.request.basket, voucher=voucher)

        # Recalculate discounts to see if the voucher gives any
        Applicator().apply(self.request.basket, self.request.user, self.request)
        discounts_after = self.request.basket.offer_applications

        found_discount = any(
            discount["voucher"] and discount["voucher"] == voucher
            for discount in discounts_after
        )
        if not found_discount:
            messages.warning(
                self.request, _("Your basket does not qualify for a voucher discount")
            )
            self.request.basket.vouchers.remove(voucher)
        else:
            messages.info(
                self.request,
                _("Voucher '%(code)s' added to basket") % {"code": voucher.code},
            )

    def form_valid(self, form):
        code = form.cleaned_data["code"]
        if not self.request.basket.id:
            return redirect_to_referrer(self.request, "basket:summary")
        if self.request.basket.contains_voucher(code):
            messages.error(
                self.request,
                _("You have already added the '%(code)s' voucher to your basket")
                % {"code": code},
            )
        else:
            try:
                voucher = self.voucher_model._default_manager.get(code=code)
            except self.voucher_model.DoesNotExist:
                messages.error(
                    self.request,
                    _("No voucher found with code '%(code)s'") % {"code": code},
                )
            else:
                self.apply_voucher_to_basket(voucher)
        return redirect_to_referrer(self.request, "basket:summary")

    def form_invalid(self, form):
        messages.error(self.request, _("Please enter a voucher code"))
        return redirect(reverse("basket:summary") + "#voucher")


class VoucherRemoveView(View):
    voucher_model = Voucher  # type: ignore
    remove_signal = voucher_removal  # type: ignore
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs) -> HttpResponseRedirect:
        """
        Handle POST request to remove a voucher from the basket.

        Args:
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments, including 'pk' for voucher ID.

        Returns:
            HttpResponseRedirect: Redirects to 'basket:summary' with appropriate messages.
        """
        voucher_id: str = kwargs["pk"]
        basket = request.basket

        # Check if basket exists and is saved
        if not basket.id:
            messages.error(request, _("Cannot remove voucher: Basket is not saved."))
            return self._redirect_to_summary()

        # Attempt to remove voucher
        try:
            voucher = basket.vouchers.get(id=voucher_id)
            basket.vouchers.remove(voucher)
            self._notify_voucher_removed(basket, voucher)
            messages.info(request, _("Voucher '%s' removed from basket") % voucher.code)
        except ObjectDoesNotExist:
            messages.error(request, _("No voucher found with id '%s'") % voucher_id)

        return self._redirect_to_summary()

    def _redirect_to_summary(self) -> HttpResponseRedirect:
        """Helper method to redirect to basket summary page."""
        return redirect("basket:summary")

    def _notify_voucher_removed(self, basket, voucher) -> None:
        """Helper method to send removal signal."""
        self.remove_signal.send(sender=self, basket=basket, voucher=voucher)


class SavedView(ModelFormSetView):
    model = Line
    basket_model = Basket
    formset_class = SavedLineFormSet
    form_class = SavedLineForm
    factory_kwargs = {"extra": 0, "can_delete": True}

    def get(self, request, *args, **kwargs):
        return redirect("basket:summary")

    def get_queryset(self):
        """
        Return list of :py:class:`Line <oscar.apps.basket.abstract_models.AbstractLine>`
        instances associated with the saved basked associated with the currently
        authenticated user.
        """  # noqa: E501
        try:
            saved_basket = self.basket_model.saved.get(owner=self.request.user)
            saved_basket.strategy = self.request.strategy
            return saved_basket.all_lines()
        except self.basket_model.DoesNotExist:
            return []

    def get_success_url(self):
        return safe_referrer(self.request, "basket:summary")

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs["prefix"] = "saved"
        kwargs["basket"] = self.request.basket
        kwargs["strategy"] = self.request.strategy
        return kwargs

    def formset_valid(self, formset):
        offers_before = self.request.basket.applied_offers()

        is_move = False
        for form in formset:
            if form.cleaned_data.get("move_to_basket", False):
                is_move = True
                msg = render_to_string(
                    "eta/basket/messages/line_restored.html", {"line": form.instance}
                )
                messages.info(self.request, msg, extra_tags="safe noicon")
                real_basket = self.request.basket
                real_basket.merge_line(form.instance)

        if not is_move:
            return super().formset_valid(formset)
        # As we're changing the basket, we need to check if it qualifies
        # for any new offers.
        BasketMessageGenerator().apply_messages(self.request, offers_before)
        return redirect(self.get_success_url())

    def formset_invalid(self, formset):
        messages.error(
            self.request,
            "\n".join(
                error for ed in formset.errors for el in ed.values() for error in el
            ),
        )
        return redirect_to_referrer(self.request, "basket:summary")
