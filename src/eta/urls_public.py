from django.conf.urls import i18n
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

admin.autodiscover()


def handler403(request):
    return render(request, "eta/403.html", status=403)


def handler404(request):
    return render(request, "eta/404.html", status=404)


def handler500(request):
    return render(request, "eta/500.html", status=500)


urlpatterns = [
    # Include admin as convenience. It's unsupported and only included
    # for developers.
    path("admin/", admin.site.urls),
    # i18n URLS need to live outside of i18n_patterns scope of Oscar
    path("i18n/", include(i18n)),
]
