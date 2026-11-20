import pytest

from unittest.mock import patch, MagicMock
from mp_api.client.contribs.client import validate_email, ContribsClient, email_format
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
    with ContribsClient(host=host, headers={"a": "b"}) as client:
        spec = client.swagger_spec
        headers = spec.http_client.session.headers
        assert headers.get("Content-Type") == "application/json"
        assert headers.get("a") == "b"
        assert spec.origin_url == f"http://{host}/apispec.json"
        assert spec.spec_dict["host"] == host
        assert spec.spec_dict["schemes"] == ["http"]
        assert spec.user_defined_formats["email"] == email_format

    host = "contribs-apis:10000"
    with ContribsClient(host=host) as client:
        spec = client.swagger_spec
        headers = spec.http_client.session.headers
        assert headers.get("Content-Type") == "application/json"
        assert spec.origin_url == f"http://{host}/apispec.json"
        assert spec.spec_dict["host"] == host
        assert spec.spec_dict["schemes"] == ["http"]
        assert spec.user_defined_formats["email"] == email_format

    host = "192.168.0.40:10000"
    with ContribsClient(host=host) as client:
        spec = client.swagger_spec
        headers = spec.http_client.session.headers
        assert headers.get("Content-Type") == "application/json"
        assert spec.origin_url == f"http://{host}/apispec.json"
        assert spec.spec_dict["host"] == host
        assert spec.spec_dict["schemes"] == ["http"]
        assert spec.user_defined_formats["email"] == email_format

    with pytest.raises(ValueError):
        with ContribsClient(host="not.valid.org") as client:
            spec = client.swagger_spec


def test_init_columns_prefix_is_not_duplicate():
    from mp_api.client.core.exceptions import MPContribsClientError

    client = MagicMock(project="demo")
    client.projects.getProjectByName.return_value.result.return_value = {"columns": []}

    # sibling columns where one name is a prefix of the other
    ContribsClient.init_columns(client, {"a.bc": "", "a.b": None})
    payload = client.projects.updateProjectByName.call_args.kwargs["project"]
    assert {c["path"] for c in payload["columns"]} == {"data.a.b", "data.a.bc"}

    # a true duplicate (ancestor listed after its child) is still rejected
    with pytest.raises(MPContribsClientError, match="Duplicate definition"):
        ContribsClient.init_columns(client, {"a.b.c": "", "a.b": None})
