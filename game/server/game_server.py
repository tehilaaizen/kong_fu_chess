from __future__ import annotations

import asyncio
import time
import uuid
from typing import Callable

import websockets

from application.game_service import GameService
from server import schemas
from server.connection_manager import ConnectionManager
from server.message_dispatcher import MessageDispatcher, Outgoing
from server.schemas import SchemaError, parse_inbound

TICK_INTERVAL_SECONDS = 0.05  # 50 ms - the hybrid server tick


def _monotonic_ms() -> int:
    """Wall-clock milliseconds from a monotonic source - the default tick
    clock (injectable so a test can drive time by hand)."""
    return int(time.monotonic() * 1000)


class GameServer:
    """The async shell around the (synchronous, tested) dispatcher and
    broadcaster: owns the live websockets, the read loop per connection,
    the outbound send queue, and the periodic tick that advances every
    game's time. Holds no game rules - it only moves bytes and time. Its
    async methods run only against a real event loop, so they are smoke-
    tested end-to-end rather than unit-tested (same category as the GUI's
    run loop); enqueue() and the pieces it drives are unit-tested.

    Wire a Broadcaster's sink to enqueue() and subscribe it to the same
    ApplicationMessageBus the GameService publishes on (see server_main)."""

    def __init__(
        self,
        game_service: GameService,
        connection_manager: ConnectionManager,
        dispatcher: MessageDispatcher,
        now_ms: Callable[[], int] = _monotonic_ms,
    ) -> None:
        self._game_service = game_service
        self._connections = connection_manager
        self._dispatcher = dispatcher
        self._now_ms = now_ms
        self._sockets: dict[str, object] = {}
        self._outbound: asyncio.Queue[Outgoing] = asyncio.Queue()

    def enqueue(self, outgoing: Outgoing) -> None:
        """Queue one broadcast for the sender loop to deliver - the sink a
        Broadcaster pushes to (called synchronously from inside a tick)."""
        self._outbound.put_nowait(outgoing)

    async def handle_connection(self, websocket) -> None:
        """Serve one client: assign it a connection id, then read frames,
        dispatch each, and send the direct responses. On disconnect, drop
        the socket and let the dispatcher clean up - which also tells the
        opponent if a player abandoned a game in progress."""
        connection_id = uuid.uuid4().hex
        self._sockets[connection_id] = websocket
        try:
            async for raw in websocket:
                await self._handle_frame(connection_id, raw)
        except websockets.ConnectionClosed:
            pass  # the client went away (cleanly or abruptly) - a normal end, not an error
        finally:
            self._sockets.pop(connection_id, None)
            for outgoing in self._dispatcher.disconnect(connection_id):
                await self._deliver(outgoing)

    async def _handle_frame(self, connection_id: str, raw: str) -> None:
        """Parse and dispatch one inbound frame, replying with an error on
        malformed input without dropping the connection."""
        try:
            inbound = parse_inbound(raw)
        except SchemaError as error:
            await self._send(connection_id, schemas.error("BAD_MESSAGE", str(error)))
            return
        for outgoing in self._dispatcher.dispatch(connection_id, inbound):
            await self._deliver(outgoing)

    async def _sender_loop(self) -> None:
        """Drain queued broadcasts and deliver them - bridges the
        synchronous bus/broadcaster to async socket sends."""
        while True:
            outgoing = await self._outbound.get()
            await self._deliver(outgoing)

    async def _tick_loop(self) -> None:
        """Advance every game's time on a fixed interval so in-flight
        motions resolve (and broadcast) even without client traffic, and
        time out any matchmaking search that has waited too long."""
        last = self._now_ms()
        while True:
            await asyncio.sleep(TICK_INTERVAL_SECONDS)
            now = self._now_ms()
            self._game_service.tick_all(now - last)
            last = now
            for outgoing in self._dispatcher.expire_matchmaking():
                self.enqueue(outgoing)

    async def _deliver(self, outgoing: Outgoing) -> None:
        """Send one message to its connection, ignoring a send that fails
        because the connection has already gone away."""
        websocket = self._sockets.get(outgoing.connection_id)
        if websocket is None:
            return
        try:
            await websocket.send(schemas.serialize(outgoing.message))
        except websockets.WebSocketException:
            pass

    async def _send(self, connection_id: str, message: dict) -> None:
        """Send one message to a specific connection id."""
        await self._deliver(Outgoing(connection_id, message))

    async def serve(self, host: str, port: int) -> None:
        """Listen on host:port and run the sender and tick loops until
        cancelled - the process's main coroutine."""
        async with websockets.serve(self.handle_connection, host, port):
            await asyncio.gather(self._sender_loop(), self._tick_loop())
