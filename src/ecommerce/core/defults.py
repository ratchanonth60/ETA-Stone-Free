from django.utils.translation import gettext_lazy as _

PAYPAL_TYPE = "paypal"
PROXY_MAP = {PAYPAL_TYPE: "ecommerce.apps.payment.apps.PaypalConfig"}


# product
STANDALONE, PARENT, CHILD = "standalone", "parent", "child"
STRUCTURE_CHOICES_PRODUCT = (
    (STANDALONE, _("Stand-alone product")),
    (PARENT, _("Parent product")),
    (CHILD, _("Child product")),
)

# Attribute types
TEXT = "text"
INTEGER = "integer"
BOOLEAN = "boolean"
FLOAT = "float"
RICHTEXT = "richtext"
DATE = "date"
DATETIME = "datetime"
OPTION = "option"
MULTI_OPTION = "multi_option"
ENTITY = "entity"
FILE = "file"
IMAGE = "image"

TYPE_CHOICES_PRODUCT_ATTR = (
    (TEXT, _("Text")),
    (INTEGER, _("Integer")),
    (BOOLEAN, _("True / False")),
    (FLOAT, _("Float")),
    (RICHTEXT, _("Rich Text")),
    (DATE, _("Date")),
    (DATETIME, _("Datetime")),
    (OPTION, _("Option")),
    (MULTI_OPTION, _("Multi Option")),
    (ENTITY, _("Entity")),
    (FILE, _("File")),
    (IMAGE, _("Image")),
)

# options
CHECKBOX = "checkbox"
SELECT = "select"
RADIO = "radio"
MULTI_SELECT = "multi_select"

TYPE_CHOICES_OPTIONS = (
    (TEXT, _("Text")),
    (INTEGER, _("Integer")),
    (BOOLEAN, _("True / False")),
    (FLOAT, _("Float")),
    (DATE, _("Date")),
    (SELECT, _("Select")),
    (RADIO, _("Radio")),
    (MULTI_SELECT, _("Multi select")),
    (CHECKBOX, _("Checkbox")),
)

# basket
OPEN, MERGED, SAVED, FROZEN, SUBMITTED = (
    "Open",
    "Merged",
    "Saved",
    "Frozen",
    "Submitted",
)
STATUS_CHOICES_BASKET = (
    (OPEN, _("Open - currently active")),
    (MERGED, _("Merged - superceded by another basket")),
    (SAVED, _("Saved - for items to be purchased later")),
    (FROZEN, _("Frozen - the basket cannot be modified")),
    (SUBMITTED, _("Submitted - has been ordered at the checkout")),
)

# partner
OPEN, CLOSED = "Open", "Closed"
STATUS_CHOICES_STOCKALERT = (
    (OPEN, _("Open")),
    (CLOSED, _("Closed")),
)

# communication
ORDER_RELATED = "Order related"
USER_RELATED = "User related"
CATEGORY_COMMUNICATION_CHOICES = (
    (ORDER_RELATED, _("Order related")),
    (USER_RELATED, _("User related")),
)
