"""
Django settings for oasis project.

Generated by 'django-admin startproject' using Django 5.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
from os import getenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = getenv(
    "SECRET_KEY",
    "django-insecure-m&m)i4tv929!f&lm$*_r)!e&-@m87+fcfee(pze0v4ae6ry#rh",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = getenv("DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = getenv("ALLOWED_HOSTS", "*").split(" ")
CSRF_TRUSTED_ORIGINS = getenv("CSRF_TRUSTED_ORIGINS", "http://localhost").split(" ")

# Application definition

INSTALLED_APPS = [
    "inventaire.apps.InventaireConfig",
    "fontawesomefree",  # les icônes du front-end
    "django.forms",  # customs widget in templates
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",  # integration django-admin et celery
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "oasis.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

FORM_RENDERED = "django.forms.rendereds.TemplatesSetting"

WSGI_APPLICATION = "oasis.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": getenv("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": getenv("SQL_DATABASE", BASE_DIR / "db.sqlite3"),
        "USER": getenv("SQL_USER"),
        "PASSWORD": getenv("SQL_PASSWORD"),
        "HOST": getenv("SQL_HOST"),
        "PORT": getenv("SQL_PORT"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
LOGIN_URL = "inventaire:login"
LOGIN_REDIRECT_URL = "inventaire:accueil"
LOGOUT_REDIRECT_URL = "inventaire:login"

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "fr-FR"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logger
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {name} {levelname} {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "propagate": True,
            "level": "DEBUG",
        }
    },
}

# diverses constantes

MAIL_CONTACT = getenv("MAIL_CONTACT", "")
DEMO_BANNER = getenv("DEMO_BANNER", "true").lower() == "true"


# celery async workers

CELERY_BROKER_URL = getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = getenv("CELERY_RESULT_BACKEND")
CELERY_TASK_TRACK_STARTED = getenv("CELERY_TASK_TRACK_STARTED", "true").lower() == "true"
