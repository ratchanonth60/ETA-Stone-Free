from django.apps import apps
from django.conf.urls import i18n
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

admin.autodiscover()

# schema_view = get_schema_view(
#     openapi.Info(
#         title="Snippets API",
#         default_version="v1",
#         description="Test description",
#         terms_of_service="https://www.google.com/policies/terms/",
#         contact=openapi.Contact(email="contact@snippets.local"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
# )


def handler403(request, exception):
    return render(request, "eta/403.html", status=403)


def handler404(request, exception):
    return render(request, "eta/404.html", status=404)


def handler500(request):
    return render(request, "eta/500.html", status=500)


api_schema_url_patterns = []
urlpatterns = [
    # Include admin as convenience. It's unsupported and only included
    # for developers.
    path("admin/", admin.site.urls),
    # i18n URLS need to live outside of i18n_patterns scope of Oscar
    path("i18n/", include(i18n)),
    # path(
    #     "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    # ),
    # path(
    #     "swagger/",
    #     schema_view.with_ui("swagger", cache_timeout=0),
    #     name="schema-swagger-ui",
    # ),
    # path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

# urlpatterns += [
#     path("api/", include(apps.get_app_config("api").urls[0])),
# ]

# Prefix Oscar URLs with language codes
urlpatterns += i18n_patterns(
    path("", include(apps.get_app_config("ecommerce").urls[0])),
    path("api/<version>/", include(apps.get_app_config("api").urls[0])),
    prefix_default_language=False,
)
