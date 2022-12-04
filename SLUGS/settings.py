"""
Django settings for SLUGS project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import django.utils.timezone as timezone
import os
import re
import environ
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, []),
    INTERNAL_IPS=(list, []),
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INTERNAL_IPS = env("INTERNAL_IPS")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.admindocs",
    "dev_utils",
    "theme",
    "SLUGS",
    "gig",
    "employee",
    "client",
    "equipment",
    "location",
    "utils",
    "finance",
    "training",
    "nested_admin",
    "fieldsets_with_inlines",
    "crispy_forms",
    "crispy_tailwind",
    "tailwind",
    "tinymce",
    "django_unicorn",
    "unicorn",
    "dynamic_formsets",
    "debug_toolbar",
    "django_cleanup.apps.CleanupConfig",
    "import_export",
    "hijack",
    "hijack.contrib.admin",
    "djangoql",
    "jsignature",
    "adminsortable2",
    "oidc_provider",
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
    "hijack.middleware.HijackUserMiddleware",
]

ROOT_URLCONF = "SLUGS.urls"

TEMPLATE_DIRS = [
    os.path.join("SLUGS", "templates"),
    os.path.join(BASE_DIR, "SLUGS/templates"),
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": TEMPLATE_DIRS,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "SLUGS.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.dirname(BASE_DIR) + "/public/static/"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TAILWIND_APP_NAME = "theme"

AUTH_USER_MODEL = "employee.Employee"

LOGIN_REDIRECT_URL = "index"
LOGOUT_REDIRECT_URL = "index"

TINYMCE_DEFAULT_CONFIG = {
    "height": 360,
    "width": 1120,
    "cleanup_on_startup": True,
    "custom_undo_redo_levels": 20,
    "selector": "textarea",
    "plugins": """
            textcolor save link image media preview codesample contextmenu
            table code lists fullscreen  insertdatetime  nonbreaking
            contextmenu directionality searchreplace wordcount visualblocks
            visualchars code fullscreen autolink lists  charmap print  hr
            anchor pagebreak
            """,
    "toolbar1": """
            fullscreen preview bold italic underline | fontselect,
            fontsizeselect  | forecolor backcolor | alignleft alignright |
            aligncenter alignjustify | indent outdent | bullist numlist table |
            | link image media | codesample |
            """,
    "toolbar2": """
            visualblocks visualchars |
            charmap hr pagebreak nonbreaking anchor |  code |
            """,
    "contextmenu": "formats | link image",
    "menubar": True,
    "statusbar": True,
    "font_formats": "Andale Mono=andale mono,times; Arial=arial,helvetica,sans-serif; Arial Black=arial black,avant garde; Book Antiqua=book antiqua,palatino; Comic Sans MS=comic sans ms,sans-serif; Courier New=courier new,courier; Georgia=georgia,palatino; Helvetica=helvetica; Impact=impact,chicago; Rubik=rubik,sans-serif; Symbol=symbol; Tahoma=tahoma,arial,helvetica,sans-serif; Terminal=terminal,monaco; Times New Roman=times new roman,times; Trebuchet MS=trebuchet ms,geneva; Verdana=verdana,geneva; Webdings=webdings; Wingdings=wingdings,zapf dingbats",  # noqa
}

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"

CRISPY_TEMPLATE_PACK = "tailwind"

PHONENUMBER_DB_FORMAT = "NATIONAL"
PHONENUMBER_DEFAULT_REGION = "US"

LOGIN_URL = "/auth/login"
LOGIN_REDIRECT_URL = "/"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = env("SLUGS_EMAIL_ADDRESS")
EMAIL_HOST_PASSWORD = env("SLUGS_EMAIL_PASSWORD")

init_py = open(os.path.join(Path(__file__).resolve().parent, "__init__.py")).read()
VERSION = "v" + re.match("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)
now = timezone.now()
BUILD = f'b.{now.strftime("%m.%d.%y.%H.%M.%S")}UTC'

SESSION_COOKIE_AGE = 86400
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

JSIGNATURE_JQUERY = "admin"

ADMINS = [("SLUGS", "bssl.slugs@binghamtonsa.org")]

BSSL_EMAIL_ADDRESS = env("BSSL_EMAIL_ADDRESS")
BSSL_FINANCE_EMAIL_ADDRESS = env("BSSL_FINANCE_EMAIL_ADDRESS")

OIDC_USERINFO = 'SLUGS.oidc_provider_settings.userinfo'
OIDC_EXTRA_SCOPE_CLAIMS = 'SLUGS.oidc_provider_settings.CustomScopeClaims'
OIDC_IDTOKEN_INCLUDE_CLAIMS = True

CORS_ALLOWED_ORIGINS = [
    "https://wiki.bssl.binghamtonsa.org",
]

PAYCHEX_COMPANY_ID = env("PAYCHEX_COMPANY_ID")
PAYCHEX_ORG = env("PAYCHEX_ORG")
PAYCHEX_COMPANY_ID_HUMAN = env("PAYCHEX_COMPANY_ID_HUMAN")
PAYCHEX_ORG_HUMAN = env("PAYCHEX_ORG_HUMAN")

PAYCHEX_API_KEY = env("PAYCHEX_API_KEY")
PAYCHEX_API_SECRET = env("PAYCHEX_API_SECRET")