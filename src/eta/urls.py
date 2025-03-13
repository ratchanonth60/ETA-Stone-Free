"""eta URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from ecommerce.urls import handler403, handler404, handler500, urlpatterns

if settings.DEBUG:
    import debug_toolbar

    # Server statics and uploaded media
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Server statics and uploaded
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Allow error pages to be tested
    urlpatterns += [
        path("403", handler403, {"exception": Exception()}),
        path("404", handler404, {"exception": Exception()}),
        path("500", handler500),
        path("__debug__/", include(debug_toolbar.urls)),
    ]
