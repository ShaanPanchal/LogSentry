"""One JSON error format for the whole API: {"error": <code>, "detail": <message>}.

Validation errors, HTTP errors (404, 405, 413, 415...) and unexpected crashes all end up here. The real
cause of an unexpected error is written to the server log only, never sent to the client.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import FRONTEND_ORIGIN
from .schemas import ErrorResponse

logger = logging.getLogger('logsentry')

CODES = {400: 'bad_request', 404: 'not_found', 405: 'method_not_allowed', 413: 'payload_too_large',
         415: 'unsupported_media_type', 422: 'invalid_input', 500: 'internal_error'}
EXAMPLES = {
    400: 'The request could not be read.',
    404: 'Analysis not found. It may have been deleted, or the server may have restarted.',
    405: 'Method Not Allowed',
    413: 'Request body is too large.',
    415: 'Upload a .log or .txt file.',
    422: 'source: Input should be \'HDFS\' or \'BGL\'',
    500: 'Something went wrong on the server. Please try again later.',
}


def error_body(status: int, detail: str) -> dict:
    return {'error': CODES.get(status, 'http_error'), 'detail': detail}


def error_response(status: int, detail: str, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(error_body(status, detail), status_code=status, headers=headers)


def error_docs(*statuses: int) -> dict:
    """The `responses=` entry for a route, so /docs shows each error with an example body."""
    return {s: {'model': ErrorResponse, 'description': CODES[s].replace('_', ' ').capitalize(),
                'content': {'application/json': {'example': error_body(s, EXAMPLES[s])}}} for s in statuses}


def _describe(err: dict) -> str:
    """One validation problem as 'field: message'. The submitted value is deliberately not repeated."""
    field = '.'.join(str(p) for p in err['loc'] if p not in ('body', 'query', 'path'))
    return f'{field}: {err["msg"]}' if field else err['msg']


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, exc: RequestValidationError):
        return error_response(422, '; '.join(_describe(e) for e in exc.errors()))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        return error_response(exc.status_code, str(exc.detail), getattr(exc, 'headers', None))

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception):
        logger.error('Unexpected error on %s %s', request.method, request.url.path, exc_info=exc)
        # Unexpected errors are answered outside the CORS middleware, so add its header here for the front end's
        # origin only. Without it the browser would hide this response and show a network error instead.
        allowed = request.headers.get('origin') == FRONTEND_ORIGIN
        return error_response(500, EXAMPLES[500], {'access-control-allow-origin': FRONTEND_ORIGIN, 'vary': 'Origin'} if allowed else None)
