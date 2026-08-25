import json
import logging

from starlette.types import ASGIApp, Receive, Scope, Send

from wyrmwood_coffee.logging import request_context

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Buffers the request body, stamps request context (method, path) for
    RequestContextFilter, and logs one DEBUG line per request including a
    redacted payload -- payload is attached only to that line, not to the
    shared context, so it doesn't leak onto other records during the request.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        body = b""
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] != "http.request":
                break
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        replayed = False

        async def receive_with_replay():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        request_context.set({"method": scope["method"], "path": scope["path"]})

        payload = None
        if body:
            try:
                parsed = json.loads(body)
            except ValueError:
                parsed = None
            if isinstance(parsed, dict):
                payload = parsed

        extra = {"payload": payload} if payload is not None else {}
        logger.debug("Request received", extra=extra)

        await self.app(scope, receive_with_replay, send)
