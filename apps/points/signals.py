"""Signale der Punkte für andere Apps (z. B. Benachrichtigungen), ohne dass Punkte sie kennen."""

from django.dispatch import Signal

# Nach dem Commit eines Rückflusses. Argumente: returns (list[ReturnedPoints]), measure.
points_returned = Signal()
