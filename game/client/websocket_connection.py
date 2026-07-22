from __future__ import annotations

import asyncio
import json
import queue
import threading

import websockets


class WebSocketConnection:
    """A ServerConnection backed by a real WebSocket, run on a background
    asyncio thread so the synchronous cv2 render loop never blocks on the
    network. The bridge is two thread-safe queues: send() drops a frame on
    the outbound queue (drained by the loop's sender), and the loop's
    receiver drops each arriving frame on the inbound queue, which poll()
    drains on the render thread. Because the adapter only ever touches game
    state from poll() (i.e. on the render thread), no game state is shared
    across threads - only the raw JSON frames cross, through the queues.

    This is transport-shell code (real sockets + a live event loop), in the
    same untested-by-design category as server/game_server.py; it is
    exercised by a smoke test, not unit tests."""

    def __init__(self) -> None:
        self._inbound: queue.Queue[dict] = queue.Queue()
        self._outbound: queue.Queue[dict] = queue.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._websocket = None
        self._connected = threading.Event()
        self._closed = threading.Event()

    def start(self, uri: str) -> None:
        """Open the connection on a daemon background thread and block until
        it is either established or has failed - so the caller can check
        is_closed() and then send() immediately afterward."""
        thread = threading.Thread(target=self._run, args=(uri,), daemon=True)
        thread.start()
        self._connected.wait()

    def is_closed(self) -> bool:
        """Whether the connection has failed to open or has since dropped
        (the server went away or closed the socket). Lets a caller stop
        waiting instead of polling a dead link forever."""
        return self._closed.is_set()

    def close(self) -> None:
        """Cleanly close the connection from the caller's thread (e.g. on
        quit), so the server sees the socket go away and can react."""
        if self._loop is not None and self._websocket is not None:
            asyncio.run_coroutine_threadsafe(self._websocket.close(), self._loop)

    def send(self, message: dict) -> None:
        """Queue one wire frame for delivery to the server (thread-safe)."""
        self._outbound.put(message)

    def poll(self) -> list[dict]:
        """Every frame received since the last poll, in order; never blocks."""
        drained: list[dict] = []
        while True:
            try:
                drained.append(self._inbound.get_nowait())
            except queue.Empty:
                return drained

    def _run(self, uri: str) -> None:
        """Own the background event loop for this connection's lifetime.
        Whatever happens - a failed connect or a dropped socket - mark the
        connection closed (and released the start() wait) on the way out."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve(uri))
        except Exception:
            pass  # connect refused, or the socket dropped - reported via is_closed()
        finally:
            self._closed.set()
            self._connected.set()  # unblock start() even if we never connected

    async def _serve(self, uri: str) -> None:
        """Connect, then run the receiver and sender until the socket
        closes."""
        async with websockets.connect(uri) as websocket:
            self._websocket = websocket
            self._connected.set()
            await asyncio.gather(self._receive(websocket), self._send(websocket))

    async def _receive(self, websocket) -> None:
        """Push every decoded inbound frame onto the inbound queue."""
        async for raw in websocket:
            self._inbound.put(json.loads(raw))

    async def _send(self, websocket) -> None:
        """Forward queued outbound frames to the socket, waiting for each on
        a worker thread so the loop stays free for receiving."""
        assert self._loop is not None
        while True:
            message = await self._loop.run_in_executor(None, self._outbound.get)
            await websocket.send(json.dumps(message))
