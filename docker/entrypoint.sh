#!/bin/sh
# Bringt die Datenbank auf den aktuellen Stand und startet danach den übergebenen Befehl.
set -eu

python manage.py migrate --noinput
python manage.py ensure_demo_admin
python manage.py load_demo_data
python manage.py load_demo_codes

exec "$@"
