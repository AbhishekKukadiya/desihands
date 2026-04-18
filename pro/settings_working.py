# Django settings for development
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-development-key-for-testing-only'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app1',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pro.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app1.context_processors.cart_counter',
                'app1.context_processors.categories_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'pro.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CSRF Settings for development
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:62041",
    "http://localhost:62041",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:58657",
    "http://localhost:58657",
    "http://127.0.0.1:56899",
    "http://localhost:56899",
    "http://127.0.0.1:52848",
    "http://localhost:52848",
    "http://127.0.0.1:64025",
    "http://localhost:64025",
    "http://127.0.0.1:63111",
    "http://localhost:63111",
    "http://127.0.0.1:55567",
    "http://localhost:55567",
    "http://127.0.0.1:53585",
    "http://localhost:53585",
]

CSRF_COOKIE_SECURE = False
