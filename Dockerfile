# Ein Image für Demo und Betrieb. Offizielle Basis-Images laufen auf amd64 und arm64 (Apple Silicon).
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Statische Dateien zur Build-Zeit sammeln; der Schlüssel wird dafür nur temporär gebraucht.
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput

# Rechte unabhängig vom Host setzen: Ein Checkout mit strenger umask (z. B. 600/700) wäre für
# den unprivilegierten Benutzer sonst nicht lesbar (PermissionError beim Start).
RUN useradd --system --uid 10001 --no-create-home app \
    && chmod -R a+rX,go-w /app \
    && chmod +x docker/entrypoint.sh docker/daily.sh
USER app

EXPOSE 8000
ENTRYPOINT ["docker/entrypoint.sh"]
# Ohne Control-Socket: Er bräuchte ein Home-Verzeichnis und wird hier nicht genutzt.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--no-control-socket"]
