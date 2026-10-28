from django.http import HttpRequest

from apps.access.models import Participant
from apps.access.session import current_participant


def participant(request: HttpRequest) -> dict[str, Participant | None]:
    return {"participant": current_participant(request)}
