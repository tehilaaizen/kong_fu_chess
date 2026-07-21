from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)

Handler = Callable[[object], None]


class ApplicationMessageBus:
    """In-process, synchronous pub/sub for application events - the
    server-wide bus that sits beside the engine's per-game observer
    mechanism (it never imports engine/model/rules). Publishers
    (GameService/GameSession) call publish(event); every subscribed
    handler receives every event and dispatches on its type itself.

    A handler that raises is caught and logged, never propagated, so one
    misbehaving subscriber can't stop the others (or break the game move
    that triggered the publish)."""

    def __init__(self) -> None:
        self._handlers: list[Handler] = []

    def subscribe(self, handler: Handler) -> None:
        """Register handler to receive every published event."""
        self._handlers.append(handler)

    def publish(self, event: object) -> None:
        """Deliver event to every subscribed handler, in subscription
        order, isolating and logging any handler that raises."""
        for handler in self._handlers:
            try:
                handler(event)
            except Exception:
                logger.exception("application event handler failed for %r", event)
