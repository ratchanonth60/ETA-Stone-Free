from django import template
from django.template.loader import select_template

register = template.Library()


@register.simple_tag(takes_context=True)
def render_product(context, product):
    """
    Render a product snippet as you would see in a browsing display.

    This templatetag looks for different templates depending on the UPC and
    product class of the passed product.  This allows alternative templates to
    be used for different product classes.
    """
    if not product or product.get_product_class() is None:
        # Search index is returning products that don't exist in the
        # database...
        return ""
    names = [
        f"eta/catalogue/partials/product/upc-{product.upc}.html",
        f"eta/catalogue/partials/product/class-{product.get_product_class().slug}.html",
        "eta/catalogue/partials/product.html",
    ]
    template_ = select_template(names)
    context = context.flatten()

    # Ensure the passed product is in the context as 'product'
    context["product"] = product
    return template_.render(context)
