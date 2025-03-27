import graphene
from graphene import relay

from .address.schema import Mutation as AddressMutations
from .address.schema import Query as AddressQuery
from .basket.schema import Mutation as BasketMutations
from .basket.schema import Query as BasketQuery
from .catalogue.schema import Mutation as CatalogueMutation
from .catalogue.schema import Query as CatalogueQuery
from .jwt.schema import Mutation as AuthMutations
from .jwt.schema import Query as AuthQuery


class RootMutation(
    AuthMutations,
    AddressMutations,
    BasketMutations,
    CatalogueMutation,
    graphene.ObjectType,
):
    pass


class RootQuery(
    AuthQuery, AddressQuery, BasketQuery, CatalogueQuery, graphene.ObjectType
):
    node = relay.Node.Field()


class MyCustomSchema(graphene.Schema):
    def format_error(self, error):
        # error.original_error -> คือ exception จริง ๆ (ถ้ามี)
        # error.message -> ข้อความเริ่มต้น

        formatted = super().format_error(error)  # type :ignore
        # formatted คือ dict โครงสร้าง errors ตาม spec เช่น
        # {
        #   "message": "...",
        #   "locations": [...],
        #   "path": [...],
        #   "extensions": {...}
        # }

        if "extensions" not in formatted:
            formatted["extensions"] = {}

        if hasattr(error.original_error, "code"):
            # สมมติเรายก Exception แบบ custom ที่มี `code` ติดมาด้วย
            formatted["extensions"]["code"] = error.original_error.code
        else:
            # หรือกำหนด code default
            formatted["extensions"]["code"] = "UNKNOWN_ERROR"

        return formatted


schema = MyCustomSchema(
    query=RootQuery,
    mutation=RootMutation,
)
