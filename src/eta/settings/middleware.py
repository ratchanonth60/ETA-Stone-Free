MIDDLEWARE = [
    "ecommerce.core.tenants.middleware.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # "debug_toolbar.middleware.DebugToolbarMiddleware",
    "ecommerce.middleware.FlatpageFallbackMiddleware",
    "ecommerce.middleware.BasketMiddleware",
]

ROOT_URLCONF = "eta.urls"
WSGI_APPLICATION = "eta.wsgi.application"
