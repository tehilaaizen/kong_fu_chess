# Repo: https://github.com/tehilaaizen/kong_fu_chess

from __future__ import annotations

import asyncio
import os

from application.auth_service import AuthService
from application.game_service import GameService
from application.password_hasher import PasswordHasher
from messaging.application_message_bus import ApplicationMessageBus
from persistence.sqlite.user_repository import SqliteUserRepository, connect
from server.broadcaster import Broadcaster
from server.connection_manager import ConnectionManager
from server.event_log import Emit, EventLog
from server.game_server import GameServer
from server.logging_config import configure_logging
from server.message_dispatcher import MessageDispatcher

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8765
DEFAULT_DB_PATH = "kong_fu_chess.db"


def build_server(log_emit: Emit | None = None, db_path: str = DEFAULT_DB_PATH) -> GameServer:
    """Composition root: build the one application bus, the GameService
    that publishes on it, the connection registry, a SQLite-backed
    AuthService, the dispatcher, and the GameServer - then wire a
    Broadcaster's sink to the server's send queue and subscribe it to the
    bus. When log_emit is given, an EventLog is also subscribed so every
    game event is logged through it. Returned unstarted so a smoke test can
    drive the pieces without opening a socket."""
    bus = ApplicationMessageBus()
    game_service = GameService(bus)
    connections = ConnectionManager()
    auth_service = AuthService(SqliteUserRepository(connect(db_path)), PasswordHasher())
    dispatcher = MessageDispatcher(game_service, connections, auth_service)
    server = GameServer(game_service, connections, dispatcher)

    broadcaster = Broadcaster(game_service, connections, server.enqueue)
    bus.subscribe(broadcaster.handle)
    if log_emit is not None:
        bus.subscribe(EventLog(log_emit).handle)
    return server


async def main(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Configure logging, then build and run the server until interrupted.
    The accounts database path can be overridden via the KFC_DB environment
    variable (defaults to kong_fu_chess.db)."""
    emit = configure_logging()
    db_path = os.environ.get("KFC_DB", DEFAULT_DB_PATH)
    emit(f"server listening on {host}:{port} (accounts db: {db_path})")
    server = build_server(log_emit=emit, db_path=db_path)
    await server.serve(host, port)


if __name__ == "__main__":
    asyncio.run(main())
