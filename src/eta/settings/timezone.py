# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/
import os

from .base import BASE_DIR

LANGUAGE_CODE = "en"

TIME_ZONE = "Asia/Bangkok"

USE_I18N = True

USE_L10N = False

USE_TZ = True

# Includes all languages that have >50% coverage in Transifex
# Taken from Django's default setting for LANGUAGES

LOCALE_PATHS = [os.path.join(BASE_DIR, 'locale')]


def gettext_noop(s):
    return s


LANGUAGES = (
    # ("ar", gettext_noop("Arabic")),
    # ("ca", gettext_noop("Catalan")),
    # ("cs", gettext_noop("Czech")),
    # ("da", gettext_noop("Danish")),
    # ("de", gettext_noop("German")),
    # ("en-gb", gettext_noop("British English")),
    # ("el", gettext_noop("Greek")),
    # ("es", gettext_noop("Spanish")),
    # ("fi", gettext_noop("Finnish")),
    # ("fr", gettext_noop("French")),
    # ("it", gettext_noop("Italian")),
    # ("ko", gettext_noop("Korean")),
    # ("nl", gettext_noop("Dutch")),
    # ("pl", gettext_noop("Polish")),
    # ("pt", gettext_noop("Portuguese")),
    # ("pt-br", gettext_noop("Brazilian Portuguese")),
    # ("ro", gettext_noop("Romanian")),
    # ("ru", gettext_noop("Russian")),
    # ("sk", gettext_noop("Slovak")),
    ("th", gettext_noop("Thailand")),
    # ("uk", gettext_noop("Ukrainian")),
    ("en", gettext_noop("English")),
    # ("zh-cn", gettext_noop("Simplified Chinese")),
)
