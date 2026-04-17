import pytest

from unittest.mock import patch, MagicMock
from mpcontribs.client import validate_email, Client, email_format
from swagger_spec_validator.common import SwaggerValidationError


def test_validate_email():
    validate_email("google:phuck@lbl.gov")
    with pytest.raises(SwaggerValidationError):
        validate_email("not-an-email!")
        validate_email("fake:info@example.com")


@patch(
    "bravado.swagger_model.Loader.load_spec",
    new=MagicMock(
        return_value={
            "swagger": "2.0",
            "paths": {},
            "info": {"title": "Swagger", "version": "0.0"},
        }
    ),
)
def test_mock():
    host = "localhost:10000"
    with Client(host=host, headers={"a": "b"}) as client:
        spec = client.swagger_spec
        headers = spec.http_client.session.headers
        assert headers.get("Content-Type") == "application/json"
        assert headers.get("a") == "b"
        assert spec.origin_url == f"http://{host}/apispec.json"
        assert spec.spec_dict["host"] == host
        assert spec.spec_dict["schemes"] == ["http"]
        assert spec.user_defined_formats["email"] == email_format

    host = "contribs-apis:10000"
    with Client(host=host) as client:
        spec = client.swagger_spec
        headers = spec.http_client.session.headers
        assert headers.get("Content-Type") == "application/json"
        assert spec.origin_url == f"http://{host}/apispec.json"
        assert spec.spec_dict["host"] == host
        assert spec.spec_dict["schemes"] == ["http"]
        assert spec.user_defined_formats["email"] == email_format

    host = "192.168.0.40:10000"
    with Client(host=host) as client:
        spec = client.swagger_spec
        headers = spec.http_client.session.headers
        assert headers.get("Content-Type") == "application/json"
        assert spec.origin_url == f"http://{host}/apispec.json"
        assert spec.spec_dict["host"] == host
        assert spec.spec_dict["schemes"] == ["http"]
        assert spec.user_defined_formats["email"] == email_format

    with pytest.raises(ValueError):
        with Client(host="not.valid.org") as client:
            spec = client.swagger_spec
