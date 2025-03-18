import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required

from ecommerce.apps.address.filters import CountryFilter, UserAddressFilter
from ecommerce.apps.address.models import Country, UserAddress

from .types import CountryType, UserAddressType


class AddressQueries(graphene.ObjectType):
    filter = DjangoFilterConnectionField(
        UserAddressType,
        filterset_class=UserAddressFilter,
        order_by=graphene.List(of_type=graphene.String),  # เพิ่ม argument สำหรับ order_by
        description="List all user addresses with filtering and ordering",
    )
    by_id = graphene.Field(
        UserAddressType,
        id=graphene.Int(required=True),
        description="Get user address by ID",
    )
    all_countries = DjangoFilterConnectionField(
        CountryType,
        filterset_class=CountryFilter,
        description="List all countries with filtering",
    )
    country_by_code = graphene.Field(
        CountryType,
        iso_3166_1_a2=graphene.String(required=True),
        description="Get country by ISO 3166-1 alpha-2 code",
    )

    @login_required
    def resolve_all_user(root, info, order_by=None, **kwargs):
        qs = UserAddress.objects.all()  # type: ignore
        if not info.context.user.is_staff:
            qs = qs.filter(user=info.context.user)

        # ใช้ filterset เพื่อกรองและเรียงลำดับ
        filterset = UserAddressFilter(kwargs, queryset=qs)
        if not filterset.is_valid():
            raise ValueError(filterset.errors)

        qs = filterset.qs
        if order_by:
            qs = qs.order_by(*order_by)  # ใช้ order_by จาก argument

        return qs

    @login_required
    def resolve_by_id(root, info, id):
        address = UserAddress.objects.get(id=id)  # type: ignore
        if info.context.user != address.user and not info.context.user.is_staff:
            raise PermissionError("You do not have permission to view this address.")
        return address

    def resolve_all_countries(root, info, **kwargs):
        return Country.objects.all()

    def resolve_country_by_code(root, info, iso_3166_1_a2):
        return Country.objects.get(iso_3166_1_a2=iso_3166_1_a2)
