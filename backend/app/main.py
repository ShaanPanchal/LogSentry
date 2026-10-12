"""FastAPI application: models load once at startup; a basic request-size limit guards uploads."""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import MAX_UPLOAD_BYTES
from .errors import EXAMPLES, error_body, register_error_handlers
from .model_service import ModelService
from .routes import router
from .store import AnalysisStore


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
        body = json.dumps(error_body(413, EXAMPLES[413])).encode()    # same JSON shape as every other error
        await send({'type': 'http.response.start', 'status': 413,
                    'headers': [(b'content-type', b'application/json'), (b'content-length', str(len(body)).encode())]})
        await send({'type': 'http.response.body', 'body': body})


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model_service = ModelService()   # once per server start, not per request
    app.state.store = AnalysisStore()          # temporary: empty again after every restart
    yield


DESCRIPTION = (
    'Log anomaly detection for HDFS and BGL logs. Upload a log, get an anomaly score for every session, '
    'then look at one session in detail.\n\n'
    'Scores are on the trained model\'s 0-1 scale and are **not probabilities**. A session is *flagged* when '
    'its score reaches the model\'s saved threshold.\n\n'
    'Analyses are stored **in memory only**: they are temporary and are lost when the server restarts. '
    'Every error uses the same JSON shape: `{"error": "<code>", "detail": "<message>"}`.')

app = FastAPI(title='LogSentry API', description=DESCRIPTION, lifespan=lifespan)
app.add_middleware(BodyLimitMiddleware, max_bytes=MAX_UPLOAD_BYTES)
register_error_handlers(app)
app.include_router(router)
