import graphene
from graphql_jwt.decorators import login_required

from ecommerce.apps.catalogue.models import Option, Product
from ecommerce.apps.partner.models import StockRecord

from .types import Basket, BasketType, Line, LineType, LineAttribute


class BasketStatusEnum(graphene.Enum):
    OPEN = "open"
    MERGED = "merged"
    SAVED = "saved"
    FROZEN = "frozen"
    SUBMITTED = "submitted"


class CreateLineMutation(graphene.Mutation):
    class Arguments:
        basket_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)
        stockrecord_id = graphene.ID(required=True)
        quantity = graphene.Int(default_value=1)
        attributes = graphene.List(graphene.JSONString, required=False)

    line = graphene.Field(LineType)

    @login_required
    def mutate(
        self, info, basket_id, product_id, stockrecord_id, quantity, attributes=None
    ):
        try:
            basket = Basket.objects.get(id=basket_id)
            if basket.owner != info.context.user:
                raise Exception("You don't have permission to modify this basket")

            product = Product.objects.get(id=product_id)
            stockrecord = StockRecord.objects.get(id=stockrecord_id)

            line = Line.objects.create(
                basket=basket,
                product=product,
                stockrecord=stockrecord,
                quantity=quantity,
                line_reference=f"{product.id}_{stockrecord.id}",  # Simple reference
            )

            if attributes:
                for attr in attributes:
                    option = Option.objects.get(id=attr.get("option_id"))
                    LineAttribute.objects.create(
                        line=line, option=option, value=attr.get("value")
                    )

            return CreateLineMutation(line=line)
        except (Basket.DoesNotExist, Product.DoesNotExist, StockRecord.DoesNotExist):
            raise Exception("Invalid basket, product, or stockrecord")


class UpdateLineMutation(graphene.Mutation):
    class Arguments:
        line_id = graphene.ID(required=True)
        quantity = graphene.Int(required=True)

    line = graphene.Field(LineType)

    @login_required
    def mutate(self, info, line_id, quantity):
        try:
            line = Line.objects.get(id=line_id)
            if line.basket.owner != info.context.user:
                raise Exception("You don't have permission to modify this line")

            line.quantity = quantity
            line.save()
            return UpdateLineMutation(line=line)
        except Line.DoesNotExist:
            raise Exception("Line not found")


class CreateBasketMutation(graphene.Mutation):
    class Arguments:
        status = BasketStatusEnum(default_value=BasketStatusEnum.OPEN)

    basket = graphene.Field(BasketType)

    @login_required
    def mutate(self, info, status=None):
        user = info.context.user
        basket = Basket.objects.create(owner=user, status=status or Basket.OPEN)
        return CreateBasketMutation(basket=basket)


class AddProductToBasketMutation(graphene.Mutation):
    class Arguments:
        basket_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)
        quantity = graphene.Int(default_value=1)

    basket = graphene.Field(BasketType)

    @login_required
    def mutate(self, info, basket_id, product_id, quantity):
        try:
            basket = Basket.objects.get(id=basket_id)
            if basket.owner != info.context.user:
                raise Exception("You don't have permission to modify this basket")

            from oscar.apps.catalogue.models import Product

            product = Product.objects.get(id=product_id)

            basket.add_product(product, quantity=quantity)
            return AddProductToBasketMutation(basket=basket)
        except Basket.DoesNotExist:
            raise Exception("Basket or Product not found")


class BasketMutation(graphene.ObjectType):
    create = CreateBasketMutation.Field()
    add_product_to_basket = AddProductToBasketMutation.Field()
    create_line = CreateLineMutation.Field()
    update_line = UpdateLineMutation.Field()
