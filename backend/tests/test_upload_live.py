"""Oversized and misleading requests sent over a real socket to a real uvicorn server (not the in-process client),
so the HTTP layer's own handling of Content-Length is part of what is tested."""
import socket
import threading
import time

import pytest
import uvicorn

from app import config
from app.main import app

BOUNDARY = b'B'
PREFIX = (b'--B\r\nContent-Disposition: form-data; name="source"\r\n\r\nHDFS\r\n'
          b'--B\r\nContent-Disposition: form-data; name="file"; filename="a.log"\r\nContent-Type: text/plain\r\n\r\n')
OVER = config.MAX_REQUEST_BYTES + 2 * 1024 * 1024        # 2 MiB more than the server accepts


@pytest.fixture(scope='module')
def server():
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    server = uvicorn.Server(uvicorn.Config(app, log_level='warning'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    thread.start()
    for _ in range(200):
        if server.started:
            break
        time.sleep(0.05)
    yield sock.getsockname()
    server.should_exit = True
    thread.join(10)


def request(address, head: bytes, body_chunks=(), timeout=20):
    """Send a raw request; keep sending body chunks until the server answers or closes. Returns (status, sent)."""
    s = socket.create_connection(address, timeout=timeout)
    sent = 0
    try:
        s.sendall(head)
        for chunk in body_chunks:
            try:
                s.sendall(chunk)
                sent += len(chunk)
            except OSError:                     # the server stopped reading and closed: exactly what we want
                break
        reply = b''
        while b'\r\n' not in reply:
            part = s.recv(4096)
            if not part:
                break
            reply += part
        return int(reply.split(b' ')[1]) if reply else None, sent
    finally:
        s.close()


def headers(**extra):
    lines = [b'POST /api/analyses HTTP/1.1', b'Host: test', b'Content-Type: multipart/form-data; boundary=B']
    lines += [f'{k.replace("_", "-")}: {v}'.encode() for k, v in extra.items()]
    return b'\r\n'.join(lines) + b'\r\n\r\n'


def mib_chunks(total):
    yield PREFIX
    for _ in range(total // (1024 * 1024)):
        yield b'x' * (1024 * 1024)


def test_declared_oversized_body_is_refused_without_sending_it(server):
    status, sent = request(server, headers(Content_Length=OVER))          # headers only, no body at all
    assert status == 413 and sent == 0


def test_chunked_oversized_body_is_refused_while_streaming(server):
    def chunked():
        for c in mib_chunks(OVER):
            yield f'{len(c):x}\r\n'.encode() + c + b'\r\n'
        yield b'0\r\n\r\n'
    status, _ = request(server, headers(Transfer_Encoding='chunked'), chunked())
    assert status == 413


def test_understated_content_length_cannot_smuggle_a_big_body(server):
    # Claims 300 bytes, then tries to send 7 MiB. The server reads only the 300 declared bytes, which hold an
    # incomplete form (refused: 422 "file: Field required", or 400 if the multipart framing itself is broken), and
    # closes the connection, so the remaining megabytes are never taken in.
    s = socket.create_connection(server, timeout=20)
    try:
        s.sendall(headers(Content_Length=300) + (PREFIX + b'x' * 300)[:300])
        reply = s.recv(4096)
        assert reply.split(b' ')[1] in (b'400', b'422'), reply[:80]
        sent = 0
        with pytest.raises(OSError):                 # the server has closed: the rest cannot be delivered
            for _ in range(OVER // (1024 * 1024)):
                s.sendall(b'x' * (1024 * 1024))
                sent += 1024 * 1024
                time.sleep(0.01)
            s.recv(1)                                # if every send was buffered, reading shows the closed connection
            raise OSError('connection still open')   # pragma: no cover (should not get here)
        assert sent < OVER
    finally:
        s.close()


def test_invalid_content_length_is_refused(server):
    status, _ = request(server, headers(Content_Length='abc'), [PREFIX])
    assert status == 400


def test_server_still_works_afterwards(server):
    status, _ = request(server, b'GET /docs HTTP/1.1\r\nHost: test\r\nConnection: close\r\n\r\n')
    assert status == 200
