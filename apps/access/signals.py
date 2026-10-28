"""Signale des Zugangs für andere Apps, ohne dass der Zugang diese kennen muss."""

from django.dispatch import Signal

# Erster Besuch an einem neuen Tag. Argumente: participant, previous_active_at.
participant_active_again = Signal()
