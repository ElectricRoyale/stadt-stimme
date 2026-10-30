#!/bin/sh
# Scheduler ohne cron: führt run_daily_tasks einmal beim Start und danach täglich zur Uhrzeit
# DAILY_TASKS_AT (UTC, Standard 02:00) aus. Die Aufgaben sind idempotent.
set -eu

run_at="${DAILY_TASKS_AT:-02:00}"

run() {
    python manage.py run_daily_tasks || echo "Tägliche Aufgaben fehlgeschlagen, nächster Versuch morgen." >&2
}

run
while true; do
    now=$(date -u +%s)
    next=$(date -u -d "today ${run_at}" +%s)
    if [ "$next" -le "$now" ]; then
        next=$(date -u -d "tomorrow ${run_at}" +%s)
    fi
    sleep $((next - now))
    run
done
