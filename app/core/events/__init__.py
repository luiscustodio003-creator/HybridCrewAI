"""API pública do módulo de eventos."""

from app.core.events.bus import EventBus, EventBusError, EventSink
from app.core.events.jsonl_sink import JsonlSink, read_events
from app.core.events.models import (
    Event,
    EventContext,
    EventError,
    EventLevel,
    EventValidationError,
    new_event,
)

__all__ = [
    "Event",
    "EventBus",
    "EventBusError",
    "EventContext",
    "EventError",
    "EventLevel",
    "EventSink",
    "EventValidationError",
    "JsonlSink",
    "new_event",
    "read_events",
]
