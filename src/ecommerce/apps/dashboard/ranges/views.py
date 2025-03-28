from io import TextIOWrapper

from django.conf import settings
from django.contrib import messages
from django.core import exceptions
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import HttpResponse, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View
from oscar.core.loading import get_classes
from oscar.views.generic import BulkEditMixin

from ecommerce.apps.catalogue.models import Product
from ecommerce.apps.offer.models import Range, RangeProduct, RangeProductFileUpload

RangeForm, RangeProductForm = get_classes(
    "dashboard.ranges.forms", ["RangeForm", "RangeProductForm"]
)


class RangeListView(ListView):
    model = Range
    context_object_name = "ranges"
    template_name = "eta/dashboard/ranges/range_list.html"
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE


class RangeCreateView(CreateView):
    model = Range
    template_name = "eta/dashboard/ranges/range_form.html"
    form_class = RangeForm

    def get_success_url(self):
        if "action" in self.request.POST:
            return reverse("dashboard:range-products", kwargs={"pk": self.object.id})
        msg = render_to_string(
            "eta/dashboard/ranges/messages/range_saved.html", {"range": self.object}
        )
        messages.success(self.request, msg, extra_tags="safe noicon")
        return reverse("dashboard:range-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = _("Create range")
        return ctx


class RangeUpdateView(UpdateView):
    model = Range
    template_name = "eta/dashboard/ranges/range_form.html"
    form_class = RangeForm

    def get_object(self):
        obj = super().get_object()
        if not obj.is_editable:
            raise exceptions.PermissionDenied("Not allowed")
        return obj

    def get_success_url(self):
        if "action" in self.request.POST:
            return reverse("dashboard:range-products", kwargs={"pk": self.object.id})
        msg = render_to_string(
            "eta/dashboard/ranges/messages/range_saved.html", {"range": self.object}
        )
        messages.success(self.request, msg, extra_tags="safe noicon")
        return reverse("dashboard:range-list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["range"] = self.object
        ctx["title"] = self.object.name
        return ctx


class RangeDeleteView(DeleteView):
    model = Range
    template_name = "eta/dashboard/ranges/range_delete.html"
    context_object_name = "range"

    def get_success_url(self):
        messages.warning(self.request, _("Range deleted"))
        return reverse("dashboard:range-list")


class RangeProductListView(BulkEditMixin, ListView):
    model = Product
    template_name = "eta/dashboard/ranges/range_product_list.html"
    context_object_name = "products"
    actions = ("remove_selected_products", "add_products")
    form_class = RangeProductForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        if request.POST.get("action", None) == "add_products":
            return self.add_products(request)
        return super().post(request, *args, **kwargs)

    def get_range(self):
        if not hasattr(self, "_range"):
            self._range = get_object_or_404(Range, id=self.kwargs["pk"])
        return self._range

    def get_queryset(self):
        products = self.get_range().all_products()
        return products.order_by("rangeproduct__display_order")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        range_obj = self.get_range()
        ctx["range"] = range_obj
        if "form" not in ctx:
            ctx["form"] = self.form_class(range_obj)
        return ctx

    def remove_selected_products(self, request, products):
        range_obj = self.get_range()
        for product in products:
            range_obj.remove_product(product)
        num_products = len(products)
        messages.success(
            request,
            ngettext(
                "Removed %d product from range",
                "Removed %d products from range",
                num_products,
            )
            % num_products,
        )
        return HttpResponseRedirect(self.get_success_url(request))

    def add_products(self, request):
        range_obj = self.get_range()  # Rename the variable to 'range_obj'
        form = self.form_class(range_obj, request.POST, request.FILES)
        if not form.is_valid():
            ctx = self.get_context_data(form=form, object_list=self.object_list)
            return self.render_to_response(ctx)

        self.handle_query_products(request, range_obj, form)  # Pass 'range_obj' instead of 'range'
        self.handle_file_products(request, range_obj, form)  # Pass 'range_obj' instead of 'range'
        return HttpResponseRedirect(self.get_success_url(request))

    def handle_query_products(self, request, range, form):
        products = form.get_products()
        if not products:
            return

        for product in products:
            range.add_product(product)

        num_products = len(products)
        messages.success(
            request,
            ngettext(
                "%d product added to range", "%d products added to range", num_products
            )
            % num_products,
        )
        if dupe_skus := form.get_duplicate_skus():
            messages.warning(
                request,
                _(
                    "The products with SKUs or UPCs matching %s are already "
                    "in this range"
                )
                % ", ".join(dupe_skus),
            )

        if missing_skus := form.get_missing_skus():
            messages.warning(
                request,
                _("No product(s) were found with SKU or UPC matching %s")
                % ", ".join(missing_skus),
            )
        self.check_imported_products_sku_duplicates(request, products)

    def handle_file_products(self, request, range, form):
        if "file_upload" not in request.FILES:
            return
        f = request.FILES["file_upload"]
        upload = self.create_upload_object(request, range, f)
        products = upload.process(TextIOWrapper(f, encoding=request.encoding))
        if not upload.was_processing_successful():
            messages.error(request, upload.error_message)
        else:
            msg = render_to_string(
                "eta/dashboard/ranges/messages/range_products_saved.html",
                {"range": range, "upload": upload},
            )
            messages.success(request, msg, extra_tags="safe noicon block")
        self.check_imported_products_sku_duplicates(request, products)

    def create_upload_object(self, request, range, f):
        return RangeProductFileUpload.objects.create(
            range=range, uploaded_by=request.user, filepath=f.name, size=f.size
        )

    def check_imported_products_sku_duplicates(self, request, queryset):
        if dupe_sku_products := (
            queryset.values("stockrecords__partner_sku")
            .annotate(total=Count("stockrecords__partner_sku"))
            .filter(total__gt=1)
            .order_by("stockrecords__partner_sku")
        ):
            dupe_skus = [p["stockrecords__partner_sku"] for p in dupe_sku_products]
            messages.warning(
                request,
                _("There are more than one product with SKU %s") % ", ".join(dupe_skus),
            )


class RangeReorderView(View):
    def post(self, request, pk):
        order = dict(request.POST).get("product")
        self._save_page_order(order)
        return HttpResponse(status=200)

    def _save_page_order(self, order):
        """
        Save the order of the products within range.
        """
        range_products = RangeProduct.objects.filter(
            range_id=self.kwargs["pk"], product_id__in=order
        )
        for range_product in range_products:
            range_product.display_order = order.index(str(range_product.product_id))
        RangeProduct.objects.bulk_update(range_products, ["display_order"])
