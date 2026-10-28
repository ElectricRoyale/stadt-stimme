"""Django-Einstellungen für StadtStimme.

Alle umgebungsabhängigen Werte kommen aus Umgebungsvariablen (siehe .env.example).
Die Standardwerte sind für die lokale Entwicklung gedacht, nicht für den Betrieb.
"""

from pathlib import Path

from config.env import env_bool, env_int, env_list, env_str

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = env_bool("DJANGO_DEBUG", default=False)

# Demo-Modus: aktiviert den Django Admin mit Demo-Zugang (ADR-001, Admin-Login zurückgestellt).
# Nur für lokale Vorführungen und die Abgabe, nie für einen öffentlichen Betrieb.
DEMO_MODE = env_bool("STADTSTIMME_DEMO_MODE", default=False)
DEMO_DATA_DIR = BASE_DIR / "data" / "demo"

# Name der Stadt, wie er auf den Seiten und im Brief erscheint.
CITY_NAME = env_str("STADTSTIMME_CITY_NAME", default="Musterstadt")

# Kartenkacheln für das Dashboard (ADR-012). Der Browser lädt sie direkt vom Kachelserver.
MAP_TILE_URL = env_str(
    "STADTSTIMME_MAP_TILE_URL", default="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
)
MAP_ATTRIBUTION = env_str(
    "STADTSTIMME_MAP_ATTRIBUTION",
    default='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>-Mitwirkende',
)

# Ohne DEBUG muss ein eigener Schlüssel gesetzt sein, sonst bricht der Start ab.
_DEV_SECRET_KEY = "dev-only-insecure-secret-key"  # noqa: S105
SECRET_KEY = env_str("DJANGO_SECRET_KEY", default=_DEV_SECRET_KEY if DEBUG else None)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "import_export",
    "apps.core",
    "apps.catalog",
    "apps.access",
    "apps.points",
    "apps.reporting",
    "apps.proposals",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.access.context_processors.participant",
                "apps.core.context_processors.city",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env_str("POSTGRES_HOST", default="localhost"),
        "PORT": env_int("POSTGRES_PORT", default=5432),
        "NAME": env_str("POSTGRES_DB", default="stadtstimme"),
        "USER": env_str("POSTGRES_USER", default="stadtstimme"),
        "PASSWORD": env_str("POSTGRES_PASSWORD", default="stadtstimme"),
        "CONN_MAX_AGE": env_int("POSTGRES_CONN_MAX_AGE", default=60),
        "CONN_HEALTH_CHECKS": True,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

EMAIL_HOST = env_str("EMAIL_HOST", default="localhost")
EMAIL_PORT = env_int("EMAIL_PORT", default=1025)
EMAIL_HOST_USER = env_str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=False)
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", default="StadtStimme <noreply@localhost>")

# Zugang per Code (ADR-001). Schlüssel für die Code-Hashes: eigener Wert empfohlen, weil ein
# Wechsel alle bisher ausgegebenen Codes ungültig macht. Ohne eigenen Wert gilt SECRET_KEY.
ACCESS_CODE_PEPPER = env_str("STADTSTIMME_CODE_PEPPER", default=SECRET_KEY)
ACCESS_MAX_FAILED_ATTEMPTS = env_int("STADTSTIMME_MAX_FAILED_ATTEMPTS", default=10)
ACCESS_LOCKOUT_MINUTES = env_int("STADTSTIMME_LOCKOUT_MINUTES", default=60)

# Punkte verfallen nach so vielen Tagen ohne Aktivität (ADR-003).
POINTS_EXPIRY_DAYS = env_int("STADTSTIMME_POINTS_EXPIRY_DAYS", default=183)

# Vorschläge (ADR-014). Prüffrist und Schwelle sind Platzhalter, bis die Stadt sie festlegt.
PROPOSAL_REVIEW_DAYS = env_int("STADTSTIMME_PROPOSAL_REVIEW_DAYS", default=14)
PROPOSAL_SUPPORT_THRESHOLD = env_int("STADTSTIMME_PROPOSAL_SUPPORT_THRESHOLD", default=50)
PROPOSALS_PER_DAY = env_int("STADTSTIMME_PROPOSALS_PER_DAY", default=5)

# Die Sitzung hält so lange wie die Punkte ohne Aktivität gelten (ADR-003: 6 Monate).
SESSION_COOKIE_AGE = env_int("STADTSTIMME_SESSION_DAYS", default=183) * 24 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = env_bool("DJANGO_SECURE_COOKIES", default=False)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env_str("DJANGO_LOG_LEVEL", default="INFO")},
}
