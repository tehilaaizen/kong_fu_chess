# Repo: https://github.com/tehilaaizen/kong_fu_chess

from __future__ import annotations

import asyncio

from application.game_service import GameService
from messaging.application_message_bus import ApplicationMessageBus
from server.broadcaster import Broadcaster
from server.connection_manager import ConnectionManager
from server.event_log import Emit, EventLog
from server.game_server import GameServer
from server.logging_config import configure_logging
from server.message_dispatcher import MessageDispatcher

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8765


def build_server(log_emit: Emit | None = None) -> GameServer:
    """Composition root: build the one application bus, the GameService
    that publishes on it, the connection registry, the dispatcher, and the
    GameServer - then wire a Broadcaster's sink to the server's send queue
    and subscribe it to the bus. When log_emit is given, an EventLog is also
    subscribed so every game event is logged through it. Returned unstarted
    so a smoke test can drive the pieces without opening a socket."""
    bus = ApplicationMessageBus()
    game_service = GameService(bus)
    connections = ConnectionManager()
    dispatcher = MessageDispatcher(game_service, connections)
    server = GameServer(game_service, connections, dispatcher)

    broadcaster = Broadcaster(game_service, connections, server.enqueue)
    bus.subscribe(broadcaster.handle)
    if log_emit is not None:
        bus.subscribe(EventLog(log_emit).handle)
    return server


async def main(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Configure logging, then build and run the server until interrupted."""
    emit = configure_logging()
    emit(f"server listening on {host}:{port}")
    server = build_server(log_emit=emit)
    await server.serve(host, port)


if __name__ == "__main__":
    asyncio.run(main())
