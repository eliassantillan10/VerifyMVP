import os
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "insecure-dev-only-secret-key"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false.")

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1,0.0.0.0,backend",
)
CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
CORS_ALLOWED_ORIGINS = env_list(
    "DJANGO_CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "apps.core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://verifymvp:verifymvp@localhost:5432/verifymvp",
)
DATABASES = {
    "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600),
}

AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CASE_BREAKER_COACH_ENABLED = env_bool("CASE_BREAKER_COACH_ENABLED", False)
CASE_BREAKER_GRADING_ENABLED = env_bool("CASE_BREAKER_GRADING_ENABLED", False)
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234").rstrip("/")
LM_STUDIO_API_TOKEN = os.getenv("LM_STUDIO_API_TOKEN", "")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "")
LM_STUDIO_GRADING_MODEL = os.getenv("LM_STUDIO_GRADING_MODEL", "")
LM_STUDIO_TIMEOUT_SECONDS = int(os.getenv("LM_STUDIO_TIMEOUT_SECONDS", "20"))
LM_STUDIO_GRADING_TIMEOUT_SECONDS = int(
    os.getenv("LM_STUDIO_GRADING_TIMEOUT_SECONDS", "90")
)
CASE_BREAKER_COACH_MAX_INPUT_CHARS = int(
    os.getenv("CASE_BREAKER_COACH_MAX_INPUT_CHARS", "2000")
)
CASE_BREAKER_COACH_MAX_OUTPUT_TOKENS = int(
    os.getenv("CASE_BREAKER_COACH_MAX_OUTPUT_TOKENS", "500")
)
CASE_BREAKER_GRADING_MAX_INPUT_CHARS = int(
    os.getenv("CASE_BREAKER_GRADING_MAX_INPUT_CHARS", "2000")
)
CASE_BREAKER_GRADING_MAX_OUTPUT_TOKENS = int(
    os.getenv("CASE_BREAKER_GRADING_MAX_OUTPUT_TOKENS", "200")
)

if CASE_BREAKER_COACH_ENABLED or CASE_BREAKER_GRADING_ENABLED:
    parsed_lm_studio_url = urlparse(LM_STUDIO_BASE_URL)
    if (
        parsed_lm_studio_url.scheme != "http"
        or parsed_lm_studio_url.hostname
        not in {"localhost", "127.0.0.1", "host.docker.internal"}
    ):
        raise RuntimeError(
            "LM_STUDIO_BASE_URL must point to a configured local LM Studio host."
        )
    if CASE_BREAKER_COACH_ENABLED and not LM_STUDIO_MODEL:
        raise RuntimeError(
            "LM_STUDIO_MODEL must be set when the Case Breaker coach is enabled."
        )
    if CASE_BREAKER_GRADING_ENABLED and not LM_STUDIO_GRADING_MODEL:
        raise RuntimeError(
            "LM_STUDIO_GRADING_MODEL must be set when Case Breaker grading is enabled."
        )
