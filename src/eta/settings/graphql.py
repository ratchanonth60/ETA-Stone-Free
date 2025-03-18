from datetime import timedelta


GRAPHENE = {
    "SCHEMA": "ecommerce.graphql.schema.schema",
    "MIDDLEWARE": [
        "graphql_jwt.middleware.JSONWebTokenMiddleware",
    ],
}
GRAPHQL_JWT = {
    "JWT_VERIFY_EXPIRATION": True,
    "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
    "JWT_EXPIRATION_DELTA": timedelta(hours=5),
    "JWT_REFRESH_EXPIRATION_DELTA": timedelta(days=7),
    "JWT_AUTH_HEADER_PREFIX": "Bearer",
}
