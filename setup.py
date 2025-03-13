import os

from setuptools import find_packages, setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup_requires = ["setuptools_scm"]

# Categorizing the dependencies
aws = [
    "boto3==1.34.11",
]

django_related = [
    "django==4.2.8",
    "django-allauth==0.59.0",
    "django-anymail[amazon_ses]==10.2",
    "django-appconf==1.0.6",
    "django-celery-beat==2.5.0",
    "django-celery-results==2.5.1",
    "django-compressor==4.4",
    "django-debug-toolbar==4.2.0",
    "django-filter==23.5",
    "django-modeltranslation==0.18.11",
    "django-oscar-api==3.2.4",
    "django-oscar[sorl-thumbnail]==3.2.2",
    "django-otp==1.3.0",
    "django-prettyjson==0.4.1",
    "django-regex-redirects==0.4.0",
    "django-reversion==5.0.10",
    "django-storages==1.14.2",
    "django-tenants==3.6.1",
    "django-utils-six==2.0",
    "django-watchman==1.3.0",
    "django-redis==5.4.0",
    "djangorestframework==3.14.0",
    "drf-yasg==1.21.7",
]

email_communication = [
    "email-reply-parser==0.5.12",
    "email-validator==2.1.0.post1",
]

data_processing_analytics = [
    "pandas==2.1.4",
    "python-dateutil==2.8.2",
    "pycountry==23.12.11",
]

caching_performance = [
    "celery==5.3.6",
    "redis==5.0.1",
    "python-memcached==1.61",
]

utilities_miscellaneous = [
    "easy-thumbnails==2.8.5",
    "hashids==1.3.1",
    "isort==5.13.2",
    "jedi==0.19.1",
    "libsass==0.22.0",
    "lxml==5.0.0",
    "Markdown==3.5.1",
    "minfraud==2.9.0",
    "nameparser==1.1.3",
    "newrelic==9.3.0",
    "premailer==3.10.0",
    "pycurl==7.45.2",
    "raven==6.10.0",
    "sorl-thumbnail==12.9.0",
    "sparkpost==1.3.10",
    "wheel==0.37.1",
    "whitenoise==6.6.0",
    "whoosh==2.7.4",
    "xmltodict==0.13.0",
    "zeep==4.2.1",
    "gql==3.4.1",
    "pgeocode==0.4.1",
    "exrex==0.11.0",
]

database_orm = [
    "psycopg2==2.9.9",
]

payment_ecommerce = [
    "stripe==7.10.0",
]

web_server = [
    "gunicorn==21.2.0",
    "uwsgi==2.0.23",
]

version_specific = [
    "Pillow==9.5.0",
]

tests_require = [
    "unittest-xml-reporting==3.2.0",
    "ptvsd==4.3.2",
    "debugpy==1.8.0",
    "factory-boy==3.2.1",
    "django-webtest==1.9.11",
    "pytest-html==4.1.1",
    "pytest-socket==0.6.0",
    "pytest-xdist==3.5.0",
    "pytest-cov==4.1.0",
    "pytest-django==4.7.0",
    "freezegun==1.4.0",
]
# Combine all dependencies into a single list for install_requires
install_requires = (
    django_related
    + email_communication
    + data_processing_analytics
    + caching_performance
    + utilities_miscellaneous
    +
    # linting_code_quality +
    database_orm
    + payment_ecommerce
    + web_server
    + version_specific
    + aws
)

setup(
    name="django-eta",
    author="ratchanonth",
    author_email="ratchanonth60@gmail.com",
    description="",
    license="BSD",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=["setuptools_scm"],
    extras_require={
        "test": tests_require,
    },
    test_suite="src.eta",
    use_scm_version=True,
)
