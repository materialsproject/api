"""
Tests the middleware for aiohttp server
Expects pytest-aiohttp
"""
import asyncio
from aws_xray_sdk import global_sdk_config


import pytest

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.exceptions import HTTPException
from starlette.testclient import TestClient
from starlette.routing import Route
from starlette.middleware import Middleware

from aws_xray_sdk.core.emitters.udp_emitter import UDPEmitter
from aws_xray_sdk.core.async_context import AsyncContext
from aws_xray_sdk.core.models import http
from .xray_utils import get_new_stubbed_recorder
from mp_api.core.xray_middleware import XRayMiddleware


class CustomStubbedEmitter(UDPEmitter):
    """
    Custom stubbed emitter which stores all segments instead of the last one
    """

    def __init__(self, daemon_address="127.0.0.1:2000"):
        super(CustomStubbedEmitter, self).__init__(daemon_address)
        self.local = []

    def send_entity(self, entity):
        self.local.append(entity)

    def pop(self):
        try:
            return self.local.pop(0)
        except IndexError:
            return None


class ServerTest(object):
    async def handle_ok(self, request: Request) -> PlainTextResponse:
        """
        Handle / request
        """
        if "content_length" in request.query_params:
            headers = {"Content-Length": request.query_params["content_length"]}
        else:
            headers = None

        return PlainTextResponse(content="ok", headers=headers)

    async def handle_error(self, request: Request) -> PlainTextResponse:
        """
        Handle /error which returns a 404
        """
        return PlainTextResponse(content="not found", status_code=404)

    async def handle_unauthorized(self, request: Request) -> PlainTextResponse:
        """
        Handle /unauthorized which returns a 401
        """
        raise HTTPException(status_code=401)

    async def handle_exception(self, request: Request) -> PlainTextResponse:
        """
        Handle /exception which raises a KeyError
        """
        return {}["key"]

    async def handle_delay(self, request: Request) -> PlainTextResponse:
        """
        Handle /delay request
        """
        await asyncio.sleep(0.3, loop=self._loop)
        return PlainTextResponse(content="ok")


@pytest.fixture
def recorder():
    """
    Clean up context storage before and after each test run
    """

    loop = asyncio.get_event_loop()
    xray_recorder = get_new_stubbed_recorder()
    xray_recorder.configure(
        service="test", sampling=False, context=AsyncContext(loop=loop)
    )

    xray_recorder.clear_trace_entities()
    yield xray_recorder

    global_sdk_config.set_sdk_enabled(True)
    xray_recorder.clear_trace_entities()


@pytest.fixture
def client(recorder):
    test_object = ServerTest()

    routes = [
        Route("/", test_object.handle_ok),
        Route("/error", test_object.handle_error),
        Route("/exception", test_object.handle_exception),
        Route("/unauthorized", test_object.handle_unauthorized),
        Route("/delay", test_object.handle_delay),
    ]

    app = Starlette(
        routes=routes, middleware=[Middleware(XRayMiddleware, recorder=recorder)]
    )

    return TestClient(app=app)


def test_ok_reg(client, recorder):
    """
    Test a normal response
    :param client: AioHttp test client fixture
    :param loop: Eventloop fixture
    :param recorder: X-Ray recorder fixture
    """

    resp = client.get("/")
    assert resp.status_code == 200

    segment = recorder.emitter.pop()
    assert not segment.in_progress

    request = segment.http["request"]
    response = segment.http["response"]

    assert request["method"] == "GET"
    assert request["url"] == "http://testserver/"
    assert response["status"] == 200


def test_ok_x_forwarded_for(client, recorder):
    """
    Test a normal response with x_forwarded_for headers
    :param test_client: AioHttp test client fixture
    :param loop: Eventloop fixture
    :param recorder: X-Ray recorder fixture
    """

    resp = client.get("/", headers={"X-Forwarded-For": "foo"})
    assert resp.status_code == 200

    segment = recorder.emitter.pop()
    assert segment.http["request"]["client_ip"] == "foo"
    assert segment.http["request"]["x_forwarded_for"]


def test_ok_content_length(client, recorder):
    """
    Test a normal response with content length as response header
    :param test_client: AioHttp test client fixture
    :param loop: Eventloop fixture
    :param recorder: X-Ray recorder fixture
    """

    resp = client.get("/?content_length=100")
    assert resp.status_code == 200

    segment = recorder.emitter.pop()
    assert segment.http["response"]["content_length"] == 100


def test_error(client, recorder):
    """
    Test a 4XX response
    :param test_client: AioHttp test client fixture
    :param loop: Eventloop fixture
    :param recorder: X-Ray recorder fixture
    """

    resp = client.get("/error")
    assert resp.status_code == 404

    segment = recorder.emitter.pop()
    assert not segment.in_progress
    assert segment.error

    request = segment.http["request"]
    response = segment.http["response"]
    assert request["method"] == "GET"
    assert request["url"] == "http://testserver/error"
    assert request["client_ip"] == "testclient:50000"
    assert response["status"] == 404


def test_exception(client, recorder):
    """
    Test handling an exception
    :param test_client: AioHttp test client fixture
    :param loop: Eventloop fixture
    :param recorder: X-Ray recorder fixture
    """

    exc = None
    try:
        client.get("/exception")
    except Exception as e:

        exc = e

    assert exc is not None

    segment = recorder.emitter.pop()
    assert not segment.in_progress
    assert segment.fault

    request = segment.http["request"]
    response = segment.http["response"]
    exception = segment.cause["exceptions"][0]
    assert request["method"] == "GET"
    assert request["url"] == "http://testserver/exception"
    assert request["client_ip"] == "testclient:50000"
    assert response["status"] == 500
    assert exception.type == "KeyError"


def test_unhauthorized(client, recorder):
    """
    Test a 401 response
    :param test_client: AioHttp test client fixture
    :param loop: Eventloop fixture
    :param recorder: X-Ray recorder fixture
    """

    resp = client.get("/unauthorized")
    assert resp.status_code == 401

    segment = recorder.emitter.pop()
    assert not segment.in_progress
    assert segment.error

    request = segment.http["request"]
    response = segment.http["response"]
    assert request["method"] == "GET"
    assert request["url"] == "http://testserver/unauthorized"
    assert request["client_ip"] == "testclient:50000"
    assert response["status"] == 401


def test_response_trace_header(client, recorder):
    resp = client.get("/")
    xray_header = resp.headers[http.XRAY_HEADER]
    segment = recorder.emitter.pop()

    expected = "Root=%s" % segment.trace_id
    assert expected in xray_header


@pytest.mark.asyncio
async def test_concurrent(client, recorder):
    """
    Test multiple concurrent requests
    :param test_client: AioHttp test client fixture
    :param loop: Eventloop fixture
    :param recorder: X-Ray recorder fixture
    """
    recorder.emitter = CustomStubbedEmitter()

    async def get_delay():
        resp = await client.get("/delay")
        assert resp.status_code == 200

    await asyncio.wait(
        [
            get_delay(),
            get_delay(),
            get_delay(),
            get_delay(),
            get_delay(),
            get_delay(),
            get_delay(),
            get_delay(),
            get_delay(),
        ]
    )

    # Ensure all ID's are different
    ids = [item.id for item in recorder.emitter.local]
    assert len(ids) == len(set(ids))


def test_disabled_sdk(client, recorder):
    """
    Test a normal response when the SDK is disabled.
    :param test_client: AioHttp test client fixture
    :param loop: Eventloop fixture
    :param recorder: X-Ray recorder fixture
    """
    global_sdk_config.set_sdk_enabled(False)

    resp = client.get("/")
    assert resp.status_code == 200

    segment = recorder.emitter.pop()
    assert not segment
