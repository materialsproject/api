from starlette.types import ASGIApp
from starlette.requests import Request
from starlette.responses import Response
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from aws_xray_sdk.core.models import http
from aws_xray_sdk.core.utils import stacktrace
from aws_xray_sdk.ext.util import (
    calculate_sampling_decision,
    calculate_segment_name,
    construct_xray_header,
    prepare_response_header,
)
from aws_xray_sdk.core.lambda_launcher import check_in_lambda, LambdaContext
from aws_xray_sdk.core import xray_recorder


class XRayMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, recorder=xray_recorder) -> None:

        super().__init__(app)
        self._recorder = recorder
        self.in_lambda_ctx = (
            True
            if check_in_lambda() and type(self._recorder.context) == LambdaContext
            else False
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Main middleware function, deals with all the X-Ray segment logic
        """

        # Create X-Ray headers
        headers = request.headers

        xray_header = construct_xray_header(headers)
        # Get name of service or generate a dynamic one from host
        name = calculate_segment_name(headers["host"].split(":", 1)[0], self._recorder)

        sampling_req = {
            "host": headers["host"],
            "method": request.method,
            "path": request.url.path,
            "service": name,
        }

        sampling_decision = calculate_sampling_decision(
            trace_header=xray_header, recorder=self._recorder, sampling_req=sampling_req
        )

        # Start a segment
        if self.in_lambda_ctx:
            segment = self._recorder.begin_subsegment(name)
        else:
            segment = self._recorder.begin_segment(
                name=name,
                traceid=xray_header.root,
                parent_id=xray_header.parent,
                sampling=sampling_decision,
            )

        # Store request metadata in the current segment
        segment.save_origin_trace_header(xray_header)
        segment.put_http_meta(http.URL, str(request.url))
        segment.put_http_meta(http.METHOD, request.method)

        if "User-Agent" in request.headers:
            segment.put_http_meta(http.USER_AGENT, request.headers["User-Agent"])

        if "X-Forwarded-For" in request.headers:
            segment.put_http_meta(http.CLIENT_IP, request.headers["X-Forwarded-For"])
            segment.put_http_meta(http.X_FORWARDED_FOR, True)
        elif "remote_addr" in request.headers:
            segment.put_http_meta(http.CLIENT_IP, request.headers["remote_addr"])
        else:
            segment.put_http_meta(
                http.CLIENT_IP, f"{request.client[0]}:{request.client[1]}"
            )

        try:
            # Call next middleware or request handler
            response = await call_next(request)

            segment.put_http_meta(http.STATUS, response.status_code)
            if "Content-Length" in response.headers:
                length = int(response.headers["Content-Length"])
                segment.put_http_meta(http.CONTENT_LENGTH, length)

            header_str = prepare_response_header(xray_header, segment)
            response.headers[http.XRAY_HEADER] = header_str
        except HTTPException as exc:
            segment.put_http_meta(http.STATUS, exc.status_code)
            raise
        except Exception as err:
            # Store exception information including the stacktrace to the segment
            segment.put_http_meta(http.STATUS, 500)
            stack = stacktrace.get_stacktrace(limit=xray_recorder.max_trace_back)
            segment.add_exception(err, stack)
            raise
        finally:

            if self.in_lambda_ctx:
                self._recorder.end_subsegment()
            else:
                self._recorder.end_segment()

        return response
