"""FastAPI application: models load once at startup; a basic request-size limit guards uploads."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import MAX_UPLOAD_BYTES
from .model_service import ModelService
from .routes import router


class _TooLarge(Exception):
    pass


class BodyLimitMiddleware:
    """Refuses request bodies over `max_bytes` with 413, including chunked bodies with no Content-Length."""

    def __init__(self, app, max_bytes: int):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)

        declared = dict(scope['headers']).get(b'content-length', b'')
        if declared.isdigit() and int(declared) > self.max_bytes:
            return await self._reject(send)

        received, started, exceeded = 0, False, False

        async def counting_receive():
            nonlocal received, exceeded
            message = await receive()
            if message['type'] == 'http.request':
                received += len(message.get('body', b''))
                if received > self.max_bytes:
                    exceeded = True
                    raise _TooLarge
            return message

        async def tracking_send(message):
            nonlocal started
            if exceeded:
                # FastAPI turns any error raised while it parses the body into a 400. Once the limit has been
                # passed, the answer is 413 whatever the app produced, and its own response is dropped.
                if not started:
                    started = True
                    await self._reject(send)
                return
            started = started or message['type'] == 'http.response.start'
            await send(message)

        try:
            await self.app(scope, counting_receive, tracking_send)
        except _TooLarge:
            if not started:
                await self._reject(send)

    async def _reject(self, send):
        body = b'{"detail":"Request body is too large."}'
        await send({'type': 'http.response.start', 'status': 413,
                    'headers': [(b'content-type', b'application/json'), (b'content-length', str(len(body)).encode())]})
        await send({'type': 'http.response.body', 'body': body})


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model_service = ModelService()   # once per server start, not per request
    yield


app = FastAPI(title='LogSentry API', lifespan=lifespan)
app.add_middleware(BodyLimitMiddleware, max_bytes=MAX_UPLOAD_BYTES)
app.include_router(router)
