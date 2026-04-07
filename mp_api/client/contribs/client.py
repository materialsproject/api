"""Define core client functionality."""

from __future__ import annotations

import functools
import gzip
import importlib.metadata
import itertools
import sys
import time
import warnings
from base64 import urlsafe_b64encode
from collections import defaultdict
from concurrent.futures import as_completed
from copy import deepcopy
from math import isclose
from pathlib import Path
from tempfile import gettempdir
from typing import TYPE_CHECKING, Literal, cast, overload
from urllib.parse import urlsplit

import orjson
import pandas as pd
import plotly.io as pio
import requests
from bravado.client import SwaggerClient
from bravado.config import bravado_config_from_config_dict
from bravado.exception import HTTPNotFound
from bravado.requests_client import RequestsClient
from bravado.swagger_model import Loader
from bravado_core.formatter import SwaggerFormat
from bravado_core.model import model_discovery
from bravado_core.resource import build_resources
from bravado_core.spec import Spec, _identity, build_api_serving_url
from bravado_core.validate import validate_object
from bson.objectid import ObjectId
from cachetools import LRUCache, cached  # type: ignore[import-untyped]
from cachetools.keys import hashkey  # type: ignore[import-untyped]
from jsonschema.exceptions import ValidationError
from pint.errors import DimensionalityError
from pyisemail import is_email
from pyisemail.diagnosis import BaseDiagnosis
from pymatgen.core import Structure as PmgStructure
from requests.exceptions import RequestException
from requests_futures.sessions import FuturesSession
from swagger_spec_validator.common import SwaggerValidationError
from tqdm.auto import tqdm
from urllib3.util.retry import Retry

from mp_api.client.contribs._types import (
    Attachment,
    MPCDict,
    MPCStructure,
    Table,
    _Component,
)
from mp_api.client.contribs._units import ureg
from mp_api.client.contribs.logger import MPCC_LOGGER, TqdmToLogger
from mp_api.client.contribs.schemas import (
    CONTRIBS_DOC_NAME,
    ContribData,
    ContribsProject,
    QueryResult,
)
from mp_api.client.contribs.settings import MPCC_SETTINGS
from mp_api.client.contribs.utils import flatten_dict, get_md5, unflatten_dict
from mp_api.client.core.exceptions import MPContribsClientError
from mp_api.client.core.schemas import _convert_to_model

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Sequence
    from typing import Any

    from mp_api.client.contribs.types import (
        AllIdMap,
        AllIdSets,
        ComponentIdSets,
        IdentifierLeaf,
        ProjectIdSets,
    )

VALID_OPS = {"query", "create", "update", "delete", "download"}
VALID_OPS_T = Literal[*VALID_OPS]  # type: ignore[valid-type]

pd.options.plotting.backend = "plotly"
pio.templates.default = "simple_white"
warnings.formatwarning = lambda msg, *args, **kwargs: f"{msg}\n"
warnings.filterwarnings("default", category=DeprecationWarning, module=__name__)


def validate_email(email_string: str):
    """Validate user email address.

    Args:
        email_string (str) : the user's email address
    """
    if email_string.count(":") != 1:
        raise SwaggerValidationError(
            f"{email_string} not of format <provider>:<email>."
        )

    provider, email = email_string.split(":", 1)
    if provider not in MPCC_SETTINGS.PROVIDERS:
        raise SwaggerValidationError(f"{provider} is not a valid provider.")

    d = is_email(email, diagnose=True)
    if d > BaseDiagnosis.CATEGORIES["VALID"]:
        raise SwaggerValidationError(f"{email} {d.message}")


# TODO: mypy has some problems with putting a bare `str`
# as a callable function in SwaggerFormat
email_format = SwaggerFormat(
    format="email",
    to_wire=str,  # type: ignore[arg-type]
    to_python=str,  # type: ignore[arg-type]
    validate=validate_email,
    description="e-mail address including provider",
)


def validate_url(
    url_string: str, qualifying: Sequence[str] = ("scheme", "netloc")
) -> None:
    """Verify an endpoint URL.

    Args:
        url_string (str) : the URL as a string
        qualifying (Sequence of str) : attributes to check for instantiation on the URL

    Returns:
        None

    Raises:
        SwaggerValidationError if any `qualifying` fields are missing

    """
    tokens = urlsplit(url_string)
    if not all(getattr(tokens, qual_attr) for qual_attr in qualifying):
        raise SwaggerValidationError(f"{url_string} invalid")


url_format = SwaggerFormat(
    format="url",
    to_wire=str,  # type: ignore[arg-type]
    to_python=str,  # type: ignore[arg-type]
    validate=validate_url,
    description="URL",
)
bravado_config_dict = {
    "validate_responses": False,
    "use_models": False,
    "include_missing_properties": False,
    "formats": [email_format, url_format],
}
bravado_config = bravado_config_from_config_dict(bravado_config_dict)
for key in set(bravado_config._fields).intersection(set(bravado_config_dict)):
    del bravado_config_dict[key]
bravado_config_dict["bravado"] = bravado_config


# https://stackoverflow.com/a/8991553
def grouper(n: int, iterable: Iterable) -> Generator:
    """Collect data into non-overlapping fixed-length chunks or blocks.

    Args:
        n (int) : Maximum number of elements per block
        iterable (Iterable) : object to divide into blocks

    Returns:
        Generator of input iterable divided into blocks
    """
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def get_session(session: requests.Session | None = None) -> FuturesSession:
    """Start a futures session.

    Args:
        session (requests.Session or None) : Optional Session to use
            in starting a FuturesSession
    Returns:
        FuturesSession
    """
    adapter_kwargs = dict(
        max_retries=Retry(
            total=MPCC_SETTINGS.RETRIES,
            read=MPCC_SETTINGS.RETRIES,
            connect=MPCC_SETTINGS.RETRIES,
            respect_retry_after_header=True,
            status_forcelist=[429, 502],  # rate limit
            allowed_methods={"DELETE", "GET", "PUT", "POST"},
            backoff_factor=2,
        )
    )
    return FuturesSession(
        session=session if session else requests.Session(),
        max_workers=MPCC_SETTINGS.MAX_WORKERS,
        adapter_kwargs=adapter_kwargs,
    )


def _response_hook(resp, *args, **kwargs):
    content_type = resp.headers["content-type"]
    if content_type == "application/json":
        result = resp.json()

        if isinstance(result, dict):
            if "data" in result and isinstance(result["data"], list):
                resp.result = result
                resp.count = len(result["data"])
            elif "count" in result and isinstance(result["count"], int):
                resp.count = result["count"]

            if "warning" in result:
                MPCC_LOGGER.warning(result["warning"])
            elif "error" in result and isinstance(result["error"], str):
                MPCC_LOGGER.error(result["error"][:10000] + "...")
        elif isinstance(result, list):
            resp.result = result
            resp.count = len(result)

    elif content_type == "application/gzip":
        resp.result = resp.content
        resp.count = 1
    else:
        MPCC_LOGGER.error(f"request failed with status {resp.status_code}!")
        resp.count = 0


def _run_futures(
    futures, total: int = 0, timeout: int = -1, desc=None, disable=False
) -> dict[str, dict[str, Any]]:
    """Helper to run futures/requests."""
    start = time.perf_counter()
    total_set = total > 0
    total = total if total_set else len(futures)
    responses: dict[str, dict[str, Any]] = {}

    with tqdm(  # type: ignore[call-arg,attr-defined]
        total=total,
        desc=desc,
        file=TqdmToLogger(),
        miniters=1,
        delay=5,
        disable=disable,
    ) as pbar:
        for future in as_completed(futures):
            if not future.cancelled():
                response = future.result()
                cnt = response.count if total_set and hasattr(response, "count") else 1
                pbar.update(cnt)

                if hasattr(future, "track_id"):
                    tid = future.track_id
                    responses[tid] = {}
                    if hasattr(response, "result"):
                        responses[tid]["result"] = response.result
                    if hasattr(response, "count"):
                        responses[tid]["count"] = response.count

                elapsed = time.perf_counter() - start
                timed_out = timeout > 0 and elapsed > timeout

                if timed_out:
                    for fut in futures:
                        fut.cancel()

    return responses


@functools.lru_cache(maxsize=1000)
def _load(protocol, host, headers_json, project, version):
    spec_dict = _raw_specs(protocol, host, version)
    headers = orjson.loads(headers_json)

    if not spec_dict["paths"]:
        url = f"{protocol}://{host}"
        origin_url = f"{url}/apispec.json"
        http_client = RequestsClient()
        http_client.session.headers.update(headers)
        swagger_spec = Spec.from_dict(
            spec_dict, origin_url, http_client, bravado_config_dict
        )
        http_client.session.close()
        return swagger_spec

    # retrieve list of projects accessible to user
    query = {"name": project} if project else {}
    query["_fields"] = ["name"]
    url = f"{protocol}://{host}"
    resp = requests.get(f"{url}/projects/", params=query, headers=headers).json()

    if not resp or not resp["data"]:
        raise MPContribsClientError(f"Failed to load projects for query {query}!")

    if project and not resp["data"]:
        raise MPContribsClientError(f"{project} doesn't exist, or access denied!")

    projects = sorted(d["name"] for d in resp["data"])
    # expand regex-based query parameters for `data` columns
    spec = _expand_params(
        protocol,
        host,
        version,
        orjson.dumps(projects),
        api_key=headers.get("x-api-key"),
    )
    spec.http_client.session.headers.update(headers)
    return spec


@functools.lru_cache(maxsize=1)
def _raw_specs(protocol, host, version):
    http_client = RequestsClient()
    url = f"{protocol}://{host}"
    origin_url = f"{url}/apispec.json"
    url4fn = origin_url.replace("apispec", f"apispec-{version}").encode("utf-8")
    fn = urlsafe_b64encode(url4fn).decode("utf-8")
    apispec = Path(gettempdir()) / fn
    spec_dict = None

    if apispec.exists():
        spec_dict = orjson.loads(apispec.read_bytes())
        MPCC_LOGGER.debug(
            f"Specs for {origin_url} and {version} re-loaded from {apispec}."
        )
    else:
        loader = Loader(http_client)
        spec_dict = loader.load_spec(origin_url)

        with apispec.open("wb") as f:
            f.write(orjson.dumps(spec_dict))

        MPCC_LOGGER.debug(f"Specs for {origin_url} and {version} saved as {apispec}.")

    if not spec_dict:
        raise MPContribsClientError(
            f"Couldn't load specs from {url} for {version}!"
        )  # not cached

    spec_dict["host"] = host
    spec_dict["schemes"] = [protocol]
    http_client.session.close()
    return spec_dict


@cached(
    cache=LRUCache(maxsize=100),
    key=lambda protocol, host, version, projects_json, **kwargs: hashkey(
        protocol, host, version, projects_json
    ),
)
def _expand_params(protocol, host, version, projects_json, api_key=None):
    columns = {"string": [], "number": []}
    projects = orjson.loads(projects_json)
    query = {"project__in": ",".join(projects)}
    query["_fields"] = "columns"
    url = f"{protocol}://{host}"
    http_client = RequestsClient()
    http_client.session.headers["Content-Type"] = "application/json"
    if api_key:
        http_client.session.headers["X-Api-Key"] = api_key
    resp = http_client.session.get(f"{url}/projects/", params=query).json()

    for proj in resp["data"]:
        for column in proj["columns"]:
            if column["path"].startswith("data."):
                col = column["path"].replace(".", "__")
                if column["unit"] == "NaN":
                    columns["string"].append(col)
                else:
                    col = f"{col}__value"
                    columns["number"].append(col)

    spec_dict = _raw_specs(protocol, host, version)
    resource = spec_dict["paths"]["/contributions/"]["get"]
    raw_params = resource.pop("parameters")
    params = {}

    for param in raw_params:
        if param["name"].startswith("^data__"):
            op = param["name"].rsplit("$__", 1)[-1]
            typ = param["type"]
            key = "number" if typ == "number" else "string"

            for column in columns[key]:
                param_name = f"{column}__{op}"
                if param_name not in params:
                    param_spec = {
                        k: v
                        for k, v in param.items()
                        if k not in ["name", "description"]
                    }
                    param_spec["name"] = param_name
                    params[param_name] = param_spec
        else:
            params[param["name"]] = param

    resource["parameters"] = list(params.values())

    origin_url = f"{url}/apispec.json"
    spec = Spec(spec_dict, origin_url, http_client, bravado_config_dict)
    model_discovery(spec)

    if spec.config["internally_dereference_refs"]:
        spec.deref = _identity
        spec._internal_spec_dict = spec.deref_flattened_spec

    for user_defined_format in spec.config["formats"]:
        spec.register_format(user_defined_format)

    spec.resources = build_resources(spec)
    spec.api_url = build_api_serving_url(
        spec_dict=spec.spec_dict,
        origin_url=spec.origin_url,
        use_spec_url_for_base_path=spec.config["use_spec_url_for_base_path"],
    )
    http_client.session.close()
    return spec


@functools.lru_cache(maxsize=1)
def _version(url):
    retries, max_retries = 0, 3
    protocol = urlsplit(url).scheme
    if "pytest" in sys.modules and protocol == "http":
        return importlib.metadata.version("mp-api")

    while retries < max_retries:
        try:
            r = requests.get(f"{url}/healthcheck", timeout=5)
            if r.status_code in {200, 403}:
                return r.json().get("version")
            else:
                retries += 1
                MPCC_LOGGER.warning(
                    f"Healthcheck for {url} failed ({r.status_code})! Wait 30s."
                )
                time.sleep(30)
        except RequestException as ex:
            retries += 1
            MPCC_LOGGER.warning(f"Could not connect to {url} ({ex})! Wait 30s.")
            time.sleep(30)


class ContribsClient(SwaggerClient):
    """client to connect to MPContribs API.

    Typical usage:
        - set environment variable MPCONTRIBS_API_KEY to the API key from your MP profile
        - import and init:
          >>> from mp_api.client.contribs.client import ContribsClient
          >>> client = ContribsClient()
    """

    def __init__(
        self,
        api_key: str | None = MPCC_SETTINGS.API_KEY,
        headers: dict | None = None,
        host: str | None = None,
        project: str | None = None,
        session: requests.Session | None = None,
        use_document_model: bool = False,
        **kwargs,
    ) -> None:
        """Initialize the client - only reloads API spec from server as needed.

        Args:
            api_key (str): API key (or use MPCONTRIBS_API_KEY env var) - ignored if headers set
            headers (dict): custom headers for localhost connections
            host (str): host address to connect to (or use MPCONTRIBS_API_HOST env var)
            project (str): use this project for all operations (query, update, create, delete)
            session (requests.Session): override session for client to use
            use_document_model (bool) : whether to use pydantic document models by default to validate data
            kwargs : To handle deprecated class attributes
        """
        # NOTE bravado future doesn't work with concurrent.futures
        # - Kong forwards consumer headers when api-key used for auth
        # - forward consumer headers when connecting through localhost

        if "apikey" in kwargs:
            api_key_warn = (
                "`apikey` has been deprecated in favor of `api_key` for "
                " consistency with the Materials Project API client."
            )
            if api_key:
                api_key_warn += (
                    " Ignoring `apikey` in favor of `api_key`, which was also set."
                )
            else:
                api_key = kwargs.pop("apikey")
            MPCC_LOGGER.warning(api_key_warn)

        if api_key and len(api_key) != 32:
            raise MPContribsClientError(f"Invalid API key: {api_key}")

        if api_key and headers:
            api_key = None
            MPCC_LOGGER.debug("headers set => ignoring apikey!")

        if not api_key and not headers:
            raise MPContribsClientError("Must specify either api_key or headers!")

        self.api_key = api_key
        self.headers = headers or {}
        self.headers = {"x-api-key": api_key} if api_key else self.headers
        self.headers["Content-Type"] = "application/json"
        self.headers_json = orjson.dumps(
            {k: self.headers[k] for k in sorted(self.headers)}
        )
        self.host = host or MPCC_SETTINGS.API_HOST
        ssl = self.host.endswith(".materialsproject.org") and not self.host.startswith(
            "localhost."
        )
        self.protocol = "https" if ssl else "http"
        self.url = f"{self.protocol}://{self.host}"
        self.project = project

        if self.url not in MPCC_SETTINGS.VALID_URLS:
            raise MPContribsClientError(
                f"{self.url} not a valid URL (one of "
                f"{', '.join(MPCC_SETTINGS.VALID_URLS)})"
            )

        self.version = _version(self.url)  # includes healthcheck
        self.session = get_session(session=session)

        self.use_document_model = use_document_model

        super().__init__(self.cached_swagger_spec)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    @property
    def apikey(self) -> str | None:
        """Handle deprecated `apikey` attr."""
        MPCC_LOGGER.warning(
            "`apikey` has been deprecated in favor of `api_key` for "
            " consistency with the Materials Project API client."
        )
        return self.api_key

    @property
    def cached_swagger_spec(self):
        return _load(
            self.protocol, self.host, self.headers_json, self.project, self.version
        )

    def __dir__(self) -> set[str]:
        members = set(self.swagger_spec.resources.keys())
        members |= {k for k in self.__dict__ if not k.startswith("_")}
        members |= {k for k in dir(self.__class__) if not k.startswith("_")}
        return members

    def _reinit(self):
        _load.cache_clear()
        super().__init__(self.cached_swagger_spec)

    def _is_valid_payload(self, model: str, data: dict) -> None:
        """Raise an error if a payload is invalid."""
        model_spec = deepcopy(self.get_model(f"{model}sSchema")._model_spec)
        model_spec.pop("required")
        model_spec["additionalProperties"] = False

        try:
            validate_object(self.swagger_spec, model_spec, data)
        except ValidationError as ex:
            raise MPContribsClientError(str(ex))

    def _is_serializable_dict(self, dct: dict) -> None:
        """Raise an error if an input dict is not JSON serializable."""
        try:
            raise MPContribsClientError(
                next(
                    f"Value {v} of {type(v)} for key {k} not supported."
                    for k, v in flatten_dict(dct).items()
                    if v is not None and not isinstance(v, (str, int, float))
                )
            )
        except StopIteration:
            pass

    def _get_per_page_default_max(
        self, op: VALID_OPS_T = "query", resource: str = "contributions"
    ) -> tuple[int, int]:
        attr = f"{op}{resource.capitalize()}"
        resource = self.swagger_spec.resources[resource]
        param_spec = getattr(resource, attr).params["per_page"].param_spec
        return param_spec["default"], param_spec["maximum"]

    def _get_per_page(
        self,
        per_page: int = -1,
        op: VALID_OPS_T = "query",
        resource: str = "contributions",
    ) -> int:
        per_page_default, per_page_max = self._get_per_page_default_max(
            op=op, resource=resource
        )
        if per_page < 0:
            per_page = per_page_default
        return min(per_page_max, per_page)

    def _split_query(
        self,
        query: dict,
        op: VALID_OPS_T = "query",
        resource: str = "contributions",
        pages: int = -1,
    ) -> list[dict]:
        """Avoid URI too long errors."""
        pp_default, pp_max = self._get_per_page_default_max(op=op, resource=resource)
        per_page = pp_default if any(k.endswith("__in") for k in query) else pp_max
        nr_params_to_split = sum(
            len(v) > per_page for v in query.values() if isinstance(v, list)
        )
        if nr_params_to_split > 1:
            raise MPContribsClientError(
                f"More than one list in query with length > {per_page} not supported!"
            )

        queries: list[dict[str, Any]] = []

        for k, v in query.items():
            if isinstance(v, list):
                line_len = len(",".join(v).encode("utf-8"))

                while line_len > 3800:
                    per_page = int(0.8 * per_page)
                    vv = v[:per_page]
                    line_len = len(",".join(vv).encode("utf-8"))

                if len(v) > per_page:
                    for chunk in grouper(per_page, v):
                        queries.append({k: list(chunk)})

        query["per_page"] = per_page

        if not queries:
            queries = [query]

        if len(queries) == 1 and pages and pages > 0:
            queries = []
            for page in range(1, pages + 1):
                queries.append(deepcopy(query))
                queries[-1]["page"] = page

        for q in queries:
            # copy over missing parameters
            q.update({k: v for k, v in query.items() if k not in q})

            # comma-separated lists
            q.update({k: ",".join(v) for k, v in q.items() if isinstance(v, list)})

        return queries

    def _get_future(
        self,
        track_id,
        params: dict,
        rel_url: str = "contributions",
        op: VALID_OPS_T = "query",
        data: dict | None = None,
    ):
        rname = rel_url.split("/", 1)[0]
        resource = self.swagger_spec.resources[rname]
        attr = f"{op}{rname.capitalize()}"
        method = getattr(resource, attr).http_method
        kwargs: dict[str, Any] = {
            "headers": self.headers,
            "params": params,
            "hooks": {"response": _response_hook},
        }

        if method == "put" and data:
            kwargs["data"] = orjson.dumps(data)

        future = getattr(self.session, method)(f"{self.url}/{rel_url}/", **kwargs)
        future.track_id = track_id
        return future

    def available_query_params(
        self,
        startswith: tuple | None = None,
        resource: str = "contributions",
    ) -> list:
        resources = self.swagger_spec.resources
        resource_obj = resources.get(resource)
        if not resource_obj:
            available_resources = list(resources.keys())
            raise MPContribsClientError(f"Choose one of {available_resources}!")

        op_key = f"query{resource.capitalize()}"
        operation = resource_obj.operations[op_key]
        params = [param.name for param in operation.params.values()]
        if not startswith:
            return params

        return [param for param in params if param.startswith(startswith)]

    def get_project(
        self, name: str | None = None, fields: list | None = None
    ) -> MPCDict | ContribsProject:
        """Retrieve a project entry.

        Args:
            name (str): name of the project
            fields (list): list of fields to include in response
        """
        name = self.project or name
        if not name:
            raise MPContribsClientError(
                "initialize client with project or set `name` argument!"
            )

        fields = fields or ["_all"]  # retrieve all fields by default
        proj = self.projects.getProjectByName(pk=name, _fields=fields).result()

        return (
            _convert_to_model(  # type: ignore[return-value]
                [proj],
                ContribsProject,
                model_name=CONTRIBS_DOC_NAME,
                requested_fields=fields,
            )[0]
            if self.use_document_model
            else MPCDict(proj)
        )

    def query_projects(
        self,
        query: dict | None = None,
        term: str | None = None,
        fields: list | None = None,
        sort: str | None = None,
        timeout: int = -1,
    ) -> list[MPCDict] | list[ContribsProject]:
        """Query projects by query and/or term (Atlas Search).

        See `client.available_query_params(resource="projects")` for keyword arguments used in
        query. Provide `term` to search for a term across all text fields in the project infos.

        Args:
            query (dict): optional query to select projects
            term (str): optional term to search text fields in projects
            fields (list): list of fields to include in response
            sort (str): field to sort by; prepend +/- for asc/desc order
            timeout (int): cancel remaining requests if timeout exceeded (in seconds)

        Returns:
            List of projects as validated `ContribsProject`s
                (use_document_model = True) and `dict`s (otherwise).
        """
        query = query or {}

        if self.project or "name" in query:
            return [self.get_project(name=query.get("name"), fields=fields)]  # type: ignore[return-value]

        if term:

            def search_future(search_term):
                future = self.session.get(
                    f"{self.url}/projects/search",
                    headers=self.headers,
                    hooks={"response": _response_hook},
                    params={"term": search_term},
                )
                future.track_id = "search"
                return future

            responses = _run_futures(
                [search_future(term)], timeout=timeout, disable=True
            )
            query["name__in"] = responses["search"].get("result", [])

        if fields:
            query["_fields"] = fields
        if sort:
            query["_sort"] = sort

        ret = self.projects.queryProjects(**query).result()  # first page
        total_count, total_pages = ret["total_count"], ret["total_pages"]

        if total_pages < 2:
            return (
                _convert_to_model(  # type: ignore[return-value]
                    ret["data"],
                    ContribsProject,
                    model_name=CONTRIBS_DOC_NAME,
                    requested_fields=fields,
                )
                if self.use_document_model
                else ret["data"]
            )

        query.update(
            {
                field: ",".join(query[field])
                for field in ["name__in", "_fields"]
                if field in query
            }
        )

        queries = []

        for page in range(2, total_pages + 1):
            queries.append(deepcopy(query))
            queries[-1]["page"] = page

        futures = [
            self._get_future(i, q, rel_url="projects") for i, q in enumerate(queries)
        ]
        responses = _run_futures(futures, total=total_count, timeout=timeout)

        ret["data"].extend([resp["result"]["data"] for resp in responses.values()])

        return (
            _convert_to_model(  # type: ignore[return-value]
                ret["data"],
                ContribsProject,
                model_name=CONTRIBS_DOC_NAME,
                requested_fields=fields,
            )
            if self.use_document_model
            else ret["data"]
        )

    def create_project(
        self, name: str, title: str, authors: str, description: str, url: str
    ) -> None:
        """Create a project.

        Args:
            name (str): unique name matching `^[a-zA-Z0-9_]{3,31}$`
            title (str): unique title with 5-30 characters
            authors (str): comma-separated list of authors
            description (str): brief description (max 2000 characters)
            url (str): URL for primary reference (paper/website/...)
        """
        queries = [{"name": name}, {"title": title}]
        for query in queries:
            if self.get_totals(query=query, resource="projects")[0]:
                raise MPContribsClientError(f"Project with {query} already exists!")

        project = ContribsProject(
            **{  # type: ignore[arg-type]
                "name": name,
                "title": title,
                "authors": authors,
                "description": description,
                "references": [{"label": "REF", "url": url}],
            }
        )
        resp = self.projects.createProject(project=project.model_dump()).result()
        owner = resp.get("owner")
        if owner:
            MPCC_LOGGER.info(f"Project `{name}` created with owner `{owner}`")
        else:
            raise MPContribsClientError(resp.get("error", resp))

    def update_project(self, update: dict, name: str | None = None) -> None:
        """Update project info.

        Args:
            update (dict): dictionary containing project info to update
            name (str): name of the project
        """
        if not update:
            MPCC_LOGGER.warning("nothing to update")
            return

        name = self.project or name
        if not name:
            raise MPContribsClientError(
                "initialize client with project or set `name` argument!"
            )

        disallowed = ["stats", "columns"]
        for k in list(update.keys()):
            if k in disallowed:
                MPCC_LOGGER.warning(f"removing `{k}` from update - not allowed.")
                update.pop(k)
                if k == "columns":
                    MPCC_LOGGER.info(
                        "use `client.init_columns()` to update project columns."
                    )
                elif k == "is_public":
                    MPCC_LOGGER.info(
                        "use `client.make_public/private()` to set `is_public`."
                    )
            elif not isinstance(update[k], bool) and not update[k]:
                MPCC_LOGGER.warning(
                    f"removing `{k}` from update - no update requested."
                )
                update.pop(k)

        if not update:
            MPCC_LOGGER.warning("nothing to update")
            return

        fields = list(self.get_model("ProjectsSchema")._properties.keys())
        for k in disallowed:
            fields.remove(k)

        fields.append("stats.contributions")
        project = self.get_project(name=name, fields=fields)

        # allow name update only if no contributions in project
        if "name" in update and project["stats"]["contributions"] > 0:
            MPCC_LOGGER.warning("removing `name` from update - not allowed.")
            update.pop("name")
            MPCC_LOGGER.error(
                "cannot change project name after contributions submitted."
            )

        payload = {
            k: v for k, v in update.items() if k in fields and project.get(k, None) != v
        }
        if not payload:
            MPCC_LOGGER.warning("nothing to update")
            return

        self._is_valid_payload("Project", payload)
        resp = self.projects.updateProjectByName(pk=name, project=payload).result()
        if not resp.get("count", 0):
            raise MPContribsClientError(resp)

    def delete_project(self, name: str | None = None) -> None:
        """Delete a project.

        Args:
            name (str): name of the project
        """
        name = self.project or name
        if not name:
            raise MPContribsClientError(
                "initialize client with project or set `name` argument!"
            )

        if not self.get_totals(query={"name": name}, resource="projects")[0]:
            raise MPContribsClientError(f"Project `{name}` doesn't exist!")

        resp = self.projects.deleteProjectByName(pk=name).result()
        if resp and "error" in resp:
            raise MPContribsClientError(resp["error"])

    def get_contribution(
        self, cid: str, fields: list | None = None
    ) -> ContribData | dict[str, Any]:  # type: ignore[return-value]
        """Retrieve a contribution.

        Args:
            cid (str): contribution ObjectID
            fields (list): list of fields to include in response

        Returns:
            ContribData if `use_document_model` and a `MPCDict` otherwise
        """
        if not fields:
            fields = list(self.get_model("ContributionsSchema")._properties.keys())
            fields.remove("needs_build")  # internal field

        contrib = self.contributions.getContributionById(
            pk=cid, _fields=fields
        ).result()
        return (
            _convert_to_model(  # type: ignore[return-value]
                [contrib],
                ContribData,
                model_name=CONTRIBS_DOC_NAME,
                requested_fields=fields,
            )[0]
            if self.use_document_model
            else MPCDict(contrib)
        )

    def get_table(self, tid_or_md5: str) -> Table:
        """Retrieve full Pandas DataFrame for a table.

        Args:
            tid_or_md5 (str): ObjectId or MD5 hash digest for table
        """
        str_len = len(tid_or_md5)
        if str_len not in {24, 32}:
            raise MPContribsClientError(
                f"'{tid_or_md5}' is not a valid table id or md5 hash!"
            )

        if str_len == 32:
            tables = self.tables.queryTables(md5=tid_or_md5, _fields=["id"]).result()
            if not tables:
                raise MPContribsClientError(f"table for md5 '{tid_or_md5}' not found!")
            tid = tables["data"][0]["id"]
        else:
            tid = tid_or_md5

        op = self.swagger_spec.resources["tables"].queryTables
        per_page = op.params["data_per_page"].param_spec["maximum"]
        table: dict[str, list[str]] = {"data": []}
        page, pages = 1, None

        while pages is None or page <= pages:
            resp = self.tables.getTableById(
                pk=tid, _fields=["_all"], data_page=page, data_per_page=per_page
            ).result()
            table["data"].extend(resp["data"])
            if pages is None:
                pages = resp["total_data_pages"]
                table["index"] = resp["index"]
                table["columns"] = resp["columns"]
                table_attrs: dict[str, str] = (resp.get("attrs") or {}) | {
                    field: resp.get(field) for field in {"id", "name", "md5"}
                }

            page += 1

        return Table.from_dict(table | {"attrs": table_attrs})

    def get_structure(self, sid_or_md5: str) -> MPCStructure:
        """Retrieve pymatgen structure.

        Args:
            sid_or_md5 (str): ObjectId or MD5 hash digest for structure
        """
        str_len = len(sid_or_md5)
        if str_len not in {24, 32}:
            raise MPContribsClientError(
                f"'{sid_or_md5}' is not a valid structure id or md5 hash!"
            )

        if str_len == 32:
            structures = self.structures.queryStructures(
                md5=sid_or_md5, _fields=["id"]
            ).result()
            if not structures:
                raise MPContribsClientError(
                    f"structure for md5 '{sid_or_md5}' not found!"
                )
            sid = structures["data"][0]["id"]
        else:
            sid = sid_or_md5

        fields = list(self.get_model("StructuresSchema")._properties.keys())
        resp = self.structures.getStructureById(pk=sid, _fields=fields).result()
        return MPCStructure.from_dict(resp)

    def get_attachment(self, aid_or_md5: str) -> Attachment:
        """Retrieve an attachment.

        Args:
            aid_or_md5 (str): ObjectId or MD5 hash digest for attachment
        """
        str_len = len(aid_or_md5)
        if str_len not in {24, 32}:
            raise MPContribsClientError(
                f"'{aid_or_md5}' is not a valid attachment id or md5 hash!"
            )

        if str_len == 32:
            attachments = self.attachments.queryAttachments(
                md5=aid_or_md5, _fields=["id"]
            ).result()
            if not attachments:
                raise MPContribsClientError(
                    f"attachment for md5 '{aid_or_md5}' not found!"
                )
            aid = attachments["data"][0]["id"]
        else:
            aid = aid_or_md5

        return Attachment(
            self.attachments.getAttachmentById(pk=aid, _fields=["_all"]).result()
        )

    def init_columns(
        self, columns: dict | None = None, name: str | None = None
    ) -> dict:
        """Initialize columns for a project to set their order and desired units.

        The `columns` field of a project tracks the minima and maxima of each `data` field
        in its contributions. If columns are not initialized before submission using this
        function, `submit_contributions` will respect the order of columns as they are
        submitted and will try to auto-determine suitable units.

        `init_columns` can be used at any point to reset the order of columns. Omitting
        the `columns` argument will re-initialize columns based on the `data` fields of
        all submitted contributions.

        The `columns` argument is a dictionary which maps the data field names to its
        units. Use `None` to indicate that a field is not a quantity (plain string). The
        unit for a dimensionless quantity is an empty string (""). Percent (`%`) and
        permille (`%%`) are considered units. Nested fields are indicated using a dot
        (".") in the data field name.

        Example:
        >>> client.init_columns({"a": None, "b.c": "eV", "b.d": "mm", "e": ""})

        This example will result in column headers on the project landing page of the form


        |      |      data       |      |
        | data |        b        | data |
        |   a  | c [eV] | d [mm] | e [] |


        Args:
            columns (dict): dictionary mapping data column to its unit
            name (str or None) : optional name of the project to use,
                defaults to `self.project`.

        Returns:
            dict containing metadata about the column updates
        """
        name = self.project or name
        if not name:
            raise MPContribsClientError(
                "initialize client with project or set `name` argument!"
            )

        columns = flatten_dict(columns or {})

        if len(columns) > MPCC_SETTINGS.MAX_COLUMNS:
            raise MPContribsClientError(
                f"Number of columns larger than {MPCC_SETTINGS.MAX_COLUMNS}!"
            )

        if not all(isinstance(v, str) for v in columns.values() if v is not None):
            raise MPContribsClientError(
                "All values in `columns` need to be None or of type str!"
            )

        new_columns = []

        if columns:
            # check columns input
            scanned_columns = set()

            for k, v in columns.items():
                if k in MPCC_SETTINGS.COMPONENTS:
                    scanned_columns.add(k)
                    continue

                nesting = k.count(".")
                if nesting > MPCC_SETTINGS.MAX_NESTING:
                    raise MPContribsClientError(
                        f"Nesting depth larger than {MPCC_SETTINGS.MAX_NESTING} for {k}!"
                    )

                for col in scanned_columns:
                    if nesting and col.startswith(k):
                        raise MPContribsClientError(
                            f"Duplicate definition of {k} in {col}!"
                        )

                    for n in range(1, nesting + 1):
                        if k.rsplit(".", n)[0] == col:
                            raise MPContribsClientError(
                                f"Ancestor of {k} already defined in {col}!"
                            )

                is_valid_string = isinstance(v, str) and v.lower() != "nan"
                if not is_valid_string and v is not None:
                    raise MPContribsClientError(
                        f"Unit '{v}' for {k} invalid (use `None` or a non-NaN string)!"
                    )

                if v != "" and v is not None and v not in ureg:
                    raise MPContribsClientError(f"Unit '{v}' for {k} not supported!")

                scanned_columns.add(k)

            # sort to avoid "overlapping columns" error in handsontable's NestedHeaders
            sorted_columns = flatten_dict(unflatten_dict(columns))
            # also sort by increasing nesting for better columns display
            sorted_columns = dict(
                sorted(sorted_columns.items(), key=lambda item: item[0].count("."))
            )

            # TODO catch unsupported column renaming or implement solution
            # reconcile with existing columns
            resp = self.projects.getProjectByName(pk=name, _fields=["columns"]).result()
            existing_columns = {}

            for col in resp["columns"]:
                path = col.pop("path")
                existing_columns[path] = col

            for path, unit in sorted_columns.items():
                if path in MPCC_SETTINGS.COMPONENTS:
                    new_columns.append({"path": path})
                    continue

                full_path = f"data.{path}"
                new_column = {"path": full_path}
                existing_column = existing_columns.get(full_path)

                if unit is not None:
                    new_column["unit"] = unit

                if existing_column:
                    # NOTE if existing_unit == "NaN":
                    #   it was set by omitting "unit" in new_column
                    new_unit = new_column.get("unit", "NaN")
                    existing_unit = existing_column.get("unit")
                    if existing_unit != new_unit:
                        if existing_unit == "NaN" and new_unit == "":
                            factor = 1
                        else:
                            conv_args = []
                            for u in [existing_unit, new_unit]:
                                try:
                                    conv_args.append(ureg.Unit(u))
                                except ValueError:
                                    raise MPContribsClientError(
                                        f"Can't convert {existing_unit} to {new_unit} for {path}"
                                    )
                            try:
                                factor = ureg.convert(1, *conv_args)  # type: ignore[arg-type]
                            except DimensionalityError:
                                raise MPContribsClientError(
                                    f"Can't convert {existing_unit} to {new_unit} for {path}"
                                )

                        if not isclose(factor, 1):
                            MPCC_LOGGER.info(
                                f"Changing {existing_unit} to {new_unit} for {path} ..."
                            )
                            # TODO scale contributions to new unit
                            raise MPContribsClientError(
                                "Changing units not supported yet. Please resubmit"
                                " contributions or update accordingly."
                            )

                new_columns.append(new_column)

        payload = {"columns": new_columns}
        self._is_valid_payload("Project", payload)

        return self.projects.updateProjectByName(pk=name, project=payload).result()

    def delete_contributions(
        self, query: dict | None = None, timeout: int = -1
    ) -> None:
        """Remove all contributions for a query.

        Args:
            query (dict): optional query to select contributions
            timeout (int): cancel remaining requests if timeout exceeded (in seconds)
        """
        if not self.project and (not query or "project" not in query):
            raise MPContribsClientError(
                "initialize client with project, or include project in query!"
            )

        tic = time.perf_counter()
        query = query or {}

        if self.project:
            query["project"] = self.project

        name = query["project"]
        project_ids = self.get_all_ids(query).get(name)
        cids = list(self._project_contrib_ids(project_ids))

        if not cids:
            MPCC_LOGGER.info(f"There aren't any contributions to delete for {name}")
            return

        total = len(cids)
        query = {"id__in": cids}
        _, total_pages = self.get_totals(query=query)
        queries = self._split_query(query, op="delete", pages=total_pages)
        futures = [self._get_future(i, q, op="delete") for i, q in enumerate(queries)]
        _run_futures(futures, total=total, timeout=timeout)
        left, _ = self.get_totals(query=query)
        deleted = total - left
        self.init_columns(name=name)
        self._reinit()
        toc = time.perf_counter()
        dt = (toc - tic) / 60
        MPCC_LOGGER.info(f"It took {dt:.1f}min to delete {deleted} contributions.")

        if left:
            raise MPContribsClientError(
                f"There were errors and {left} contributions are left to delete!"
            )

    def get_totals(
        self,
        query: dict | None = None,
        timeout: int = -1,
        resource: str = "contributions",
        op: VALID_OPS_T = "query",
    ) -> tuple[int, int]:
        """Retrieve total count and pages for resource entries matching query.

        Args:
            query (dict): query to select resource entries
            timeout (int): cancel remaining requests if timeout exceeded (in seconds)
            resource (str): type of resource
            op (str): operation to calculate total pages for, one of
                      ("query", "create", "update", "delete", "download")

        Returns:
            tuple of total counts (int) and pages (int)
        """
        if op not in VALID_OPS:
            raise MPContribsClientError(f"`op` has to be one of {VALID_OPS}")

        query = query or {}
        if self.project and "project" not in query:
            query["project"] = self.project

        skip_keys = {"per_page", "_fields", "format", "_sort"}
        query = {k: v for k, v in query.items() if k not in skip_keys}
        query["_fields"] = []  # only need totals -> explicitly request no fields
        queries = self._split_query(query, resource=resource, op=op)  # don't paginate
        futures = [
            self._get_future(i, q, rel_url=resource) for i, q in enumerate(queries)
        ]
        responses = _run_futures(futures, timeout=timeout, desc="Totals")

        result = {
            k: sum(resp.get("result", {}).get(k, 0) for resp in responses.values())
            for k in ("total_count", "total_pages")
        }

        return result["total_count"], result["total_pages"]

    def count(self, query: dict | None = None) -> int:
        """Shortcut for get_totals()."""
        return self.get_totals(query=query)[0]

    def get_unique_identifiers_flags(
        self, query: dict[str, Any] | None = None
    ) -> dict[str, bool]:
        """Retrieve values for `unique_identifiers` flags.

        See `client.available_query_params(resource="projects")` for available query parameters.

        Args:
            query (dict): query to select projects

        Returns:
            dict of str to bool, ex.:
            {"<project-name>": True|False, ...}
        """
        return {
            p["name"]: p["unique_identifiers"]
            for p in self.query_projects(
                query=query, fields=["name", "unique_identifiers"]
            )
        }

    def _get_contrib_identifier_payloads(
        self,
        query: dict[str, Any] | None = None,
        include: list[str] | None = None,
        timeout: int = -1,
        data_id_fields: dict[str, str] | None = None,
        op: VALID_OPS_T = "query",
    ) -> tuple[list[dict[str, Any]], set[str], dict[str, str], dict[str, bool]]:
        include = include or []
        components = {x for x in include if x in MPCC_SETTINGS.COMPONENTS}
        if include and not components:
            raise MPContribsClientError(
                f"`include` must be subset of {MPCC_SETTINGS.COMPONENTS}!"
            )

        if op not in VALID_OPS:
            raise MPContribsClientError(f"`op` has to be one of {VALID_OPS}")

        unique_identifiers = self.get_unique_identifiers_flags()
        data_id_fields = {
            project: field
            for project, field in (data_id_fields or {}).items()
            if project in unique_identifiers and isinstance(field, str)
        }

        query = query or {}
        if self.project and "project" not in query:
            query["project"] = self.project

        for k in ["page", "per_page", "_fields"]:
            query.pop(k, None)

        id_fields = {"project", "id", "identifier"}
        if data_id_fields:
            id_fields.update(f"data.{field}" for field in data_id_fields.values())

        query["_fields"] = list(id_fields | components)
        _, total_pages = self.get_totals(query=query, timeout=timeout)
        queries = self._split_query(query, op=op, pages=total_pages)
        futures = [self._get_future(i, q) for i, q in enumerate(queries)]
        responses = _run_futures(futures, timeout=timeout, desc="Identifiers")

        contributions: list[dict[str, Any]] = []
        for resp in responses.values():
            result = resp.get("result", {})
            data = result.get("data", [])
            if isinstance(data, list):
                contributions.extend(data)

        return contributions, components, data_id_fields, unique_identifiers

    def _collect_ids_as_sets(
        self,
        contributions: list[dict[str, Any]],
        components: set[str],
        data_id_fields: dict[str, str],
    ) -> AllIdSets:
        ret: AllIdSets = {}

        for contrib in contributions:
            project = contrib["project"]
            data_id_field = data_id_fields.get(project)

            if project not in ret:
                id_sets: ProjectIdSets = {"ids": set(), "identifiers": set()}
                if data_id_field:
                    id_sets[f"{data_id_field}_set"] = set()
                ret[project] = id_sets

            project_sets = ret[project]
            cast(set[str], project_sets["ids"]).add(contrib["id"])
            cast(set[str], project_sets["identifiers"]).add(contrib["identifier"])

            if data_id_field:
                data_value = contrib.get("data", {}).get(data_id_field)
                if isinstance(data_value, str):
                    cast(set[str], project_sets[f"{data_id_field}_set"]).add(data_value)

            for component in components:
                component_items = contrib.get(component)
                if not isinstance(component_items, list):
                    continue

                if component not in project_sets:
                    project_sets[component] = {"ids": set(), "md5s": set()}

                component_sets = cast(ComponentIdSets, project_sets[component])
                for item in component_items:
                    if not isinstance(item, dict):
                        continue
                    for idk in ("id", "md5"):
                        if isinstance(item.get(idk), str):
                            component_sets[f"{idk}s"].add(item[idk])

        return ret

    def _collect_ids_as_map(
        self,
        contributions: list[dict[str, Any]],
        components: set[str],
        data_id_fields: dict[str, str],
        unique_identifiers: dict[str, bool],
    ) -> AllIdMap:
        ret: AllIdMap = {}

        for contrib in contributions:
            project = contrib["project"]
            identifier = contrib["identifier"]
            contrib_id = contrib["id"]
            data_id_field = data_id_fields.get(project)
            data_id_field_val = contrib.get("data", {}).get(data_id_field)

            if project not in ret:
                ret[project] = {}

            project_map = ret[project]

            if unique_identifiers.get(project, False):
                entry: IdentifierLeaf = {"id": contrib_id}
                if data_id_field and isinstance(data_id_field_val, str):
                    entry[data_id_field] = data_id_field_val

                for component in components:
                    component_items = contrib.get(component)
                    if not isinstance(component_items, list):
                        continue
                    entry[component] = {
                        d["name"]: {"id": d["id"], "md5": d["md5"]}
                        for d in component_items
                        if isinstance(d, dict)
                        and all(
                            isinstance(d.get(k), str) for k in ("name", "id", "md5")
                        )
                    }

                project_map[identifier] = entry
            elif data_id_field and isinstance(data_id_field_val, str):
                entry = {"id": contrib_id}
                for component in components:
                    component_items = contrib.get(component)
                    if not isinstance(component_items, list):
                        continue
                    entry[component] = {
                        d["name"]: {"id": d["id"], "md5": d["md5"]}
                        for d in component_items
                        if isinstance(d, dict)
                        and all(
                            isinstance(d.get(k), str) for k in ("name", "id", "md5")
                        )
                    }

                project_map[identifier] = {data_id_field_val: entry}

        return ret

    @staticmethod
    def _project_contrib_ids(project_values: ProjectIdSets | None) -> set[str]:
        if not project_values:
            return set()
        ids = project_values.get("ids")
        return ids if isinstance(ids, set) else set()

    @staticmethod
    def _project_component_ids(
        project_values: ProjectIdSets | None, component: str
    ) -> set[str]:
        if not project_values:
            return set()
        component_values = project_values.get(component)
        if not isinstance(component_values, dict):
            return set()
        ids = component_values.get("ids")
        return ids if isinstance(ids, set) else set()

    @overload
    def get_all_ids(
        self,
        query: dict[str, Any] | None = None,
        include: list[str] | None = None,
        timeout: int = -1,
        data_id_fields: dict[str, str] | None = None,
        fmt: Literal["sets"] = "sets",
        op: VALID_OPS_T = "query",
    ) -> AllIdSets:
        ...

    @overload
    def get_all_ids(
        self,
        query: dict[str, Any] | None = None,
        include: list[str] | None = None,
        timeout: int = -1,
        data_id_fields: dict[str, str] | None = None,
        fmt: Literal["map"] = "map",
        op: VALID_OPS_T = "query",
    ) -> AllIdMap:
        ...

    def get_all_ids(
        self,
        query: dict[str, Any] | None = None,
        include: list[str] | None = None,
        timeout: int = -1,
        data_id_fields: dict[str, str] | None = None,
        fmt: Literal["sets", "map"] = "sets",
        op: VALID_OPS_T = "query",
    ) -> AllIdSets | AllIdMap:
        """Retrieve a list of existing contribution and component (Object)IDs.

        Args:
            query (dict): query to select contributions
            include (list): components to include in response
            timeout (int): cancel remaining requests if timeout exceeded (in seconds)
            data_id_fields (dict): map of project to extra field in `data` to include as ID field
            fmt (str): return `sets` of identifiers or `map` (see below)
            op (str): operation to calculate total pages for, one of
                      ("query", "create", "update", "delete", "download")

        Returns:
            {"<project-name>": {
                # if fmt == "sets":
                "ids": {<set of contributions IDs>},
                "identifiers": {<set of contribution identifiers>},
                "<data_id_field>_set": {<set of data_id_field values>},
                "structures|tables|attachments": {
                    "ids": {<set of structure|table|attachment IDs>},
                    "md5s": {<set of structure|table|attachment md5s>}
                },
                # if fmt == "map" and unique_identifiers=True
                "<identifier>": {
                    "id": "<contribution ID>",
                    "<data_id_field>": "<data_id_field value>",
                    "structures|tables|attachments": {
                        "<name>": {
                            "id": "<structure|table|attachment ID>",
                            "md5": "<structure|table|attachment md5>"
                        }, ...
                    }
                }
                # if fmt == "map" and unique_identifiers=False (data_id_field required)
                "<identifier>": {
                    "<data_id_field value>": {
                        "id": "<contribution ID>",
                        "structures|tables|attachments": {
                            "<name>": {
                                "id": "<structure|table|attachment ID>",
                                "md5": "<structure|table|attachment md5>"
                            }, ...
                        }
                    }, ...
                }
            }, ...}
        """
        q = deepcopy(query or {})  # prevent modifying user query
        if fmt == "sets":
            (
                contributions,
                components,
                clean_data_id_fields,
                _,
            ) = self._get_contrib_identifier_payloads(
                query=q,
                include=include,
                timeout=timeout,
                data_id_fields=data_id_fields,
                op=op,
            )
            return self._collect_ids_as_sets(
                contributions=contributions,
                components=components,
                data_id_fields=clean_data_id_fields,
            )

        if fmt == "map":
            (
                contributions,
                components,
                clean_data_id_fields,
                unique_identifiers,
            ) = self._get_contrib_identifier_payloads(
                query=q,
                include=include,
                timeout=timeout,
                data_id_fields=data_id_fields,
                op=op,
            )
            return self._collect_ids_as_map(
                contributions=contributions,
                components=components,
                data_id_fields=clean_data_id_fields,
                unique_identifiers=unique_identifiers,
            )

        raise MPContribsClientError("`fmt` must be one of {'sets', 'map'}!")

    def query_contributions(
        self,
        query: dict | None = None,
        fields: list | None = None,
        sort: str | None = None,
        paginate: bool = False,
        timeout: int = -1,
    ) -> dict[str, Any] | QueryResult:
        """Query contributions.

        See `client.available_query_params()` for keyword arguments used in query.

        Args:
            query (dict): optional query to select contributions
            fields (list): list of fields to include in response
            sort (str): field to sort by; prepend +/- for asc/desc order
            paginate (bool): paginate through all results
            timeout (int): cancel remaining requests if timeout exceeded (in seconds)

        Returns:
            List of contributions
        """
        query = query or {}

        if self.project and "project" not in query:
            query["project"] = self.project

        if paginate:
            cids: list[str] = []
            for values in self.get_all_ids(query).values():
                cids.extend(self._project_contrib_ids(values))

            if not cids:
                raise MPContribsClientError("No contributions match the query.")

            total = len(cids)
            cids_query = {"id__in": cids, "_fields": fields, "_sort": sort}
            _, total_pages = self.get_totals(query=cids_query)
            queries = self._split_query(cids_query, pages=total_pages)
            futures = [self._get_future(i, q) for i, q in enumerate(queries)]
            responses = _run_futures(futures, total=total, timeout=timeout)
            ret: dict[str, int | list[str]] = {"total_count": 0, "data": []}

            for resp in responses.values():
                result = resp["result"]
                ret["data"].extend(result["data"])  # type: ignore[union-attr]
                ret["total_count"] += result["total_count"]  # type: ignore[union-attr]
        else:
            ret = self.contributions.queryContributions(
                _fields=fields, _sort=sort, **query
            ).result()

        if len(ret["data"]) > 0 and self.use_document_model:  # type: ignore[arg-type]
            ret["data"] = [ContribData(**doc) for doc in ret["data"]]  # type: ignore[arg-type,misc,union-attr]

        return (
            _convert_to_model(  # type: ignore[return-value]
                [ret], QueryResult, model_name=CONTRIBS_DOC_NAME
            )[0]
            if self.use_document_model
            else ret
        )

    def update_contributions(
        self, data: dict, query: dict | None = None, timeout: int = -1
    ) -> dict:
        """Apply the same update to all contributions in a project (matching query).

        See `client.available_query_params()` for keyword arguments used in query.

        Args:
            data (dict): update to apply on every matching contribution
            query (dict): optional query to select contributions
            timeout (int): cancel remaining requests if timeout exceeded (in seconds)
        """
        if not data:
            raise MPContribsClientError("Nothing to update.")

        tic = time.perf_counter()
        self._is_valid_payload("Contribution", data)

        if "data" in data:
            self._is_serializable_dict(data["data"])

        query = query or {}

        if self.project:
            if "project" in query and self.project != query["project"]:
                raise MPContribsClientError(
                    f"client initialized with different project {self.project}!"
                )
            query["project"] = self.project
        else:
            if not query or "project" not in query:
                raise MPContribsClientError(
                    "initialize client with project, or include project in query!"
                )

        name = query["project"]
        project_ids = self.get_all_ids(query).get(name)
        cids = list(self._project_contrib_ids(project_ids))

        if not cids:
            raise MPContribsClientError(
                f"There aren't any contributions to update for {name}"
            )

        # get current list of data columns to decide if swagger reload is needed
        resp = self.projects.getProjectByName(pk=name, _fields=["columns"]).result()
        old_paths = {c["path"] for c in resp["columns"]}

        total = len(cids)
        cids_query = {"id__in": cids}
        _, total_pages = self.get_totals(query=cids_query)
        queries = self._split_query(cids_query, op="update", pages=total_pages)
        futures = [
            self._get_future(i, q, op="update", data=data)
            for i, q in enumerate(queries)
        ]
        responses = _run_futures(futures, total=total, timeout=timeout)
        updated = sum(resp["count"] for _, resp in responses.items())

        if updated:
            resp = self.projects.getProjectByName(pk=name, _fields=["columns"]).result()
            new_paths = {c["path"] for c in resp["columns"]}

            if new_paths != old_paths:
                self.init_columns(name=name)
                self._reinit()

        toc = time.perf_counter()
        return {"updated": updated, "total": total, "seconds_elapsed": toc - tic}

    def make_public(
        self, query: dict | None = None, recursive: bool = False, timeout: int = -1
    ) -> dict:
        """Publish a project and optionally its contributions.

        Args:
            query (dict): optional query to select contributions
            recursive (bool): also publish according contributions?
            timeout (int) : cancel remaining requests if timeout exceeded (in seconds)
        """
        return self._set_is_public(
            True, query=query, recursive=recursive, timeout=timeout
        )

    def make_private(
        self, query: dict | None = None, recursive: bool = False, timeout: int = -1
    ) -> dict:
        """Make a project and optionally its contributions private.

        Args:
            query (dict): optional query to select contributions
            recursive (bool): also make according contributions private?
            timeout (int) : cancel remaining requests if timeout exceeded (in seconds)
        """
        return self._set_is_public(
            False, query=query, recursive=recursive, timeout=timeout
        )

    def _set_is_public(
        self,
        is_public: bool,
        query: dict | None = None,
        recursive: bool = False,
        timeout: int = -1,
    ) -> dict:
        """Set the `is_public` flag for a project and optionally its contributions.

        Args:
            is_public (bool): target value for `is_public` flag
            query (dict): optional query to select contributions
            recursive (bool): also set `is_public` for according contributions?
            timeout (int): cancel remaining requests if timeout exceeded (in seconds)
        """
        if not self.project and (not query or "project" not in query):
            raise MPContribsClientError(
                "initialize client with project, or include project in query!"
            )

        query = query or {}

        if self.project:
            query["project"] = self.project

        try:
            resp = self.projects.getProjectByName(
                pk=query["project"], _fields=["is_public", "is_approved"]
            ).result()
        except HTTPNotFound:
            raise MPContribsClientError(
                f"project `{query['project']}` not found or access denied!"
            )

        if not recursive and resp["is_public"] == is_public:
            return {
                "warning": f"`is_public` already set to {is_public} for `{query['project']}`."
            }

        ret = {}

        if resp["is_public"] != is_public:
            if is_public and not resp["is_approved"]:
                raise MPContribsClientError(
                    f"project `{query['project']}` is not approved yet!"
                )

            resp = self.projects.updateProjectByName(
                pk=query["project"], project={"is_public": is_public}
            ).result()
            ret["published"] = resp["count"] == 1

        if recursive:
            query = query or {}
            query["is_public"] = not is_public
            ret["contributions"] = self.update_contributions(
                {"is_public": is_public}, query=query, timeout=timeout
            )

        return ret

    def submit_contributions(
        self,
        contributions: list[dict],
        ignore_dupes: bool = False,
        timeout: int = -1,
        skip_dupe_check: bool = False,
    ) -> None:
        """Submit a list of contributions.

        Example for a single contribution dictionary:

        {
            "project": "sandbox",
            "identifier": "mp-4",
            "data": {
                "a": "3 eV",
                "b": {"c": "hello", "d": 3}
            },
            "structures": [<pymatgen Structure>, ...],
            "tables": [<pandas DataFrame>, ...],
            "attachments": [<pathlib.Path>, <mp_api.client.contribs.Attachment>, ...]
        }

        This function can also be used to update contributions by including the respective
        contribution `id`s in the above dictionary and only including fields that need
        updating. Set list entries to `None` for components that are to be left untouched
        during an update.

        Args:
            contributions (list): list of contribution dicts to submit
            ignore_dupes (bool): force duplicate components to be submitted
            timeout (int): cancel remaining requests if timeout exceeded (in seconds)
            skip_dupe_check (bool): skip duplicate check for contribution identifiers

        Returns:
            None

        Raises:
            MPContribsClientError on malformed submitted data.
        """
        if not contributions or not isinstance(contributions, list):
            raise MPContribsClientError(
                "Please provide list of contributions to submit."
            )

        # get existing contributions
        tic = time.perf_counter()
        project_name_set: set[str] = set()
        collect_ids = []
        require_one_of = {"data"} | set(MPCC_SETTINGS.COMPONENTS)

        for idx, c in enumerate(contributions):
            has_keys = require_one_of & c.keys()
            if not has_keys:
                raise MPContribsClientError(
                    f"Nothing to submit for contribution #{idx}!"
                )
            elif not all(c[k] for k in has_keys):
                for k in has_keys:
                    if not c[k]:
                        raise MPContribsClientError(
                            f"Empty `{k}` for contribution #{idx}!"
                        )
            elif "id" in c:
                collect_ids.append(c["id"])
            elif "project" in c and "identifier" in c:
                project_name_set.add(c["project"])
            elif self.project and "project" not in c and "identifier" in c:
                project_name_set.add(self.project)
                contributions[idx]["project"] = self.project
            else:
                raise MPContribsClientError(
                    f"Provide `project` & `identifier`, or `id` for contribution #{idx}!"
                )

        id2project = {}
        if collect_ids:
            resp = self.get_all_ids(dict(id__in=collect_ids), timeout=timeout)
            project_name_set |= set(resp.keys())

            id2project.update(
                {
                    cid: project_name
                    for project_name, values in resp.items()
                    for cid in self._project_contrib_ids(values)
                }
            )

        project_names: list[str] = list(project_name_set)

        if not skip_dupe_check and len(collect_ids) != len(contributions):
            nproj = len(project_names)
            query: dict[str, Any] = (
                {"name__in": project_names} if nproj > 1 else {"name": project_names[0]}
            )
            unique_identifiers: dict[str, bool] = self.get_unique_identifiers_flags(
                query
            )
            query = (
                {"project__in": project_names}
                if nproj > 1
                else {"project": project_names[0]}
            )
            existing = self.get_all_ids(
                query, include=MPCC_SETTINGS.COMPONENTS, timeout=timeout
            )

        # prepare contributions
        contribs = defaultdict(list)
        digests: dict[str, defaultdict[str, set[str]]] = {
            project_name: defaultdict(set) for project_name in project_names
        }
        fields = [
            comp
            for comp in self.get_model("ContributionsSchema")._properties
            if comp not in MPCC_SETTINGS.COMPONENTS
        ]
        fields.remove("needs_build")  # internal field

        for contrib in tqdm(contributions, desc="Prepare"):  # type: ignore[call-arg,attr-defined]
            if "data" in contrib:
                contrib["data"] = unflatten_dict(contrib["data"])
                self._is_serializable_dict(contrib["data"])

            update = "id" in contrib
            project_name = id2project[contrib["id"]] if update else contrib["project"]
            if (
                not update
                and unique_identifiers.get(project_name)
                and contrib["identifier"]
                in existing.get(project_name, {}).get("identifiers", {})
            ):
                continue

            contrib_copy: dict[str, Any] = {}
            for k in fields:
                if k in contrib:
                    if isinstance(contrib[k], dict):
                        flat: dict[str, str | int | float] = {}
                        for kk, vv in flatten_dict(contrib[k]).items():
                            if isinstance(vv, bool):
                                flat[kk] = "Yes" if vv else "No"
                            elif (isinstance(vv, str) and vv) or isinstance(
                                vv, (float, int)
                            ):
                                flat[kk] = vv
                        contrib_copy[k] = deepcopy(unflatten_dict(flat))
                    else:
                        contrib_copy[k] = deepcopy(contrib[k])

            contribs[project_name].append(contrib_copy)

            for component in MPCC_SETTINGS.COMPONENTS:
                elements = contrib.get(component, [])
                nelems = len(elements)

                if nelems > MPCC_SETTINGS.MAX_ELEMS:
                    raise MPContribsClientError(
                        f"Too many {component} ({nelems} > {MPCC_SETTINGS.MAX_ELEMS})!"
                    )

                if update and not nelems:
                    continue  # nothing to update for this component

                contribs[project_name][-1][component] = []

                for element in elements:
                    if update and element is None:
                        contribs[project_name][-1][component].append(None)
                        continue

                    is_structure = isinstance(element, PmgStructure)
                    is_table = isinstance(element, (pd.DataFrame, Table))
                    is_attachment = isinstance(element, (str, Path, Attachment))
                    if component == "structures" and not is_structure:
                        raise MPContribsClientError(
                            f"Use pymatgen Structure for {component}!"
                        )
                    elif component == "tables" and not is_table:
                        raise MPContribsClientError(
                            f"Use pandas DataFrame or mp_api.client.contribs.Table for {component}!"
                        )
                    elif component == "attachments" and not is_attachment:
                        raise MPContribsClientError(
                            f"Use str, pathlib.Path or mp_api.client.contribs.Attachment for {component}"
                        )

                    if is_structure:
                        dct = element.as_dict()
                        del dct["@module"]
                        del dct["@class"]

                        if not dct.get("charge"):
                            del dct["charge"]

                        if "properties" in dct:
                            if dct["properties"]:
                                MPCC_LOGGER.warning(
                                    "storing structure properties not supported, yet!"
                                )
                            del dct["properties"]
                    elif is_table:
                        table = element
                        if not isinstance(table, Table):
                            table = Table(element)
                            table.attrs = element.attrs

                        table._clean()
                        dct = table.to_dict(orient="split")
                    elif is_attachment:
                        if isinstance(element, (str, Path)):
                            element = Attachment.from_file(element)

                        dct = {k: element[k] for k in ["mime", "content"]}
                    else:
                        raise MPContribsClientError("This should never happen")

                    digest = get_md5(dct)

                    if is_structure:
                        dct["name"] = getattr(element, "name", "structure")
                    elif is_table:
                        dct["name"], dct["attrs"] = table._attrs_as_dict()
                    elif is_attachment:
                        dct["name"] = element.name

                    dupe = bool(
                        digest in digests[project_name][component]
                        or digest
                        in existing.get(project_name, {})
                        .get(component, {})
                        .get("md5s", [])
                    )

                    if not ignore_dupes and dupe:
                        # TODO add matching duplicate info to msg
                        msg = f"Duplicate in {project_name}: {contrib['identifier']} {dct['name']}"
                        raise MPContribsClientError(msg)

                    digests[project_name][component].add(digest)
                    contribs[project_name][-1][component].append(dct)

                self._is_valid_payload("Contribution", contribs[project_name][-1])

        # submit contributions
        if contribs:
            total, total_processed = 0, 0
            nmax = 1000  # TODO this should be set dynamically from `bulk_update_limit`

            def post_future(track_id, payload):
                future = self.session.post(
                    f"{self.url}/contributions/",
                    headers=self.headers,
                    hooks={"response": _response_hook},
                    data=payload,
                )
                future.track_id = track_id
                return future

            def put_future(pk, payload):
                future = self.session.put(
                    f"{self.url}/contributions/{pk}/",
                    headers=self.headers,
                    hooks={"response": _response_hook},
                    data=payload,
                )
                future.track_id = pk
                return future

            for project_name in project_names:
                ncontribs = len(contribs[project_name])
                total += ncontribs
                retries = 0

                while contribs[project_name]:
                    futures: list[Any] = []
                    post_chunk: list[dict[str, Any]] = []
                    idx = 0

                    for n, c in enumerate(contribs[project_name]):
                        if "id" in c:
                            pk = c.pop("id")
                            if not c:
                                MPCC_LOGGER.error(
                                    f"SKIPPED: update of {project_name}/{pk} empty."
                                )

                            payload = orjson.dumps(c)
                            if len(payload) < MPCC_SETTINGS.MAX_PAYLOAD:
                                futures.append(put_future(pk, payload))
                            else:
                                MPCC_LOGGER.error(
                                    f"SKIPPED: update of {project_name}/{pk} too large."
                                )
                        else:
                            next_post_chunk = post_chunk + [c]
                            next_payload = orjson.dumps(next_post_chunk)
                            if (
                                len(next_post_chunk) > nmax
                                or len(next_payload) >= MPCC_SETTINGS.MAX_PAYLOAD
                            ):
                                if post_chunk:
                                    payload = orjson.dumps(post_chunk)
                                    futures.append(post_future(idx, payload))
                                    post_chunk = []
                                    idx += 1
                                else:
                                    MPCC_LOGGER.error(
                                        f"SKIPPED: contrib {project_name}/{n} too large."
                                    )
                                    continue

                            post_chunk.append(c)

                    if post_chunk and len(futures) < ncontribs:
                        payload = orjson.dumps(post_chunk)
                        futures.append(post_future(idx, payload))

                    if not futures:
                        break  # nothing to do

                    responses = _run_futures(
                        futures,
                        total=ncontribs - total_processed,
                        timeout=timeout,
                        desc="Submit",
                    )
                    processed = sum(r.get("count", 0) for r in responses.values())
                    total_processed += processed

                    if (
                        total_processed != ncontribs
                        and retries < MPCC_SETTINGS.RETRIES
                        and unique_identifiers.get(project_name)
                    ):
                        MPCC_LOGGER.info(
                            f"{total_processed}/{ncontribs} processed -> retrying ..."
                        )
                        existing[project_name] = self.get_all_ids(
                            dict(project=project_name),
                            include=MPCC_SETTINGS.COMPONENTS,
                            timeout=timeout,
                        ).get(project_name, {"identifiers": set()})
                        unique_identifiers[
                            project_name
                        ] = self.projects.getProjectByName(
                            pk=project_name, _fields=["unique_identifiers"]
                        ).result()[
                            "unique_identifiers"
                        ]
                        existing_ids = existing.get(project_name, {}).get(
                            "identifiers", []
                        )
                        contribs[project_name] = [
                            c
                            for c in contribs[project_name]
                            if c["identifier"] not in existing_ids
                        ]
                        retries += 1
                    else:
                        contribs[project_name] = []  # abort retrying
                        if total_processed != ncontribs:
                            if retries >= MPCC_SETTINGS.RETRIES:
                                MPCC_LOGGER.error(
                                    f"{project_name}: Tried {MPCC_SETTINGS.RETRIES} times - abort."
                                )
                            elif not unique_identifiers.get(project_name):
                                MPCC_LOGGER.info(
                                    f"{project_name}: resubmit failed contributions manually"
                                )
                self.init_columns(name=project_name)

            self._reinit()
            toc = time.perf_counter()
            dt = (toc - tic) / 60
            MPCC_LOGGER.info(
                f"It took {dt:.1f}min to submit {total_processed}/{total} contributions."
            )
        else:
            MPCC_LOGGER.info("Nothing to submit.")

    def download_contributions(
        self,
        query: dict | None = None,
        outdir: str | Path = MPCC_SETTINGS.DEFAULT_DOWNLOAD_DIR,
        overwrite: bool = False,
        include: list[str] | None = None,
        timeout: int = -1,
    ) -> list:
        """Download a list of contributions as .json.gz file(s).

        Args:
            query: query to select contributions
            outdir: optional output directory
            overwrite: force re-download
            include: components to include in downloads
            timeout: cancel remaining requests if timeout exceeded (in seconds)

        Returns:
            Number of new downloads written to disk.
        """
        start = time.perf_counter()
        query = query or {}
        include = include or []
        outdir = Path(outdir) or Path(".")
        outdir.mkdir(parents=True, exist_ok=True)
        components = {x for x in include if x in MPCC_SETTINGS.COMPONENTS}
        if include and not components:
            raise MPContribsClientError(
                f"`include` must be subset of {MPCC_SETTINGS.COMPONENTS}!"
            )

        all_ids = self.get_all_ids(query, include=list(components), timeout=timeout)
        fmt = query.get("format", "json")
        contributions: list[MPCDict] = []
        components_loaded: defaultdict[
            str, dict[str, MPCStructure | Table | Attachment]
        ] = defaultdict(dict)

        elapsed = float(timeout)
        for name, values in all_ids.items():
            if elapsed > 0:
                elapsed -= time.perf_counter() - start
                if elapsed < 1:
                    return contributions

                start = time.perf_counter()

            for component in components:
                if elapsed > 0:
                    elapsed -= time.perf_counter() - start
                    if elapsed < 1:
                        return contributions

                    start = time.perf_counter()

                ids = list(self._project_component_ids(values, component))
                if not ids:
                    continue

                paths = self._download_resource(
                    resource=component,
                    ids=ids,
                    fmt=fmt,
                    outdir=outdir,
                    overwrite=overwrite,
                    timeout=timeout,
                )
                MPCC_LOGGER.debug(
                    f"Downloaded {len(ids)} {component} for '{name}' in {len(paths)} file(s)."
                )

                match component:
                    case "structures":
                        component_cls: type[_Component] = MPCStructure
                    case "tables":
                        component_cls = Table
                    case "attachments":
                        component_cls = Attachment

                for path in paths:
                    with gzip.open(path, "rb") as f:
                        for c in orjson.loads(f.read()):
                            components_loaded[component][
                                c["id"]
                            ] = component_cls.from_dict(c)

            cids = list(self._project_contrib_ids(values))
            if not cids:
                continue

            paths = self._download_resource(
                resource="contributions",
                ids=cids,
                fmt=fmt,
                outdir=outdir,
                overwrite=overwrite,
                timeout=timeout,
            )
            MPCC_LOGGER.debug(
                f"Downloaded {len(cids)} contributions for '{name}' in {len(paths)} file(s)."
            )

            for path in paths:
                with gzip.open(path, "rb") as f:
                    for c in orjson.loads(f.read()):
                        contrib = MPCDict(c)
                        for component in components_loaded:
                            contrib[component] = [
                                components_loaded[component][d["id"]]
                                for d in contrib.pop(component)
                            ]

                        contributions.append(contrib)

        return contributions

    def download_structures(
        self,
        ids: list[str],
        outdir: str | Path = MPCC_SETTINGS.DEFAULT_DOWNLOAD_DIR,
        overwrite: bool = False,
        timeout: int = -1,
        fmt: Literal["json", "csv"] = "json",
    ) -> list[Path]:
        """Download a list of structures as a .json.gz file.

        Args:
            ids: list of structure ObjectIds
            outdir: optional output directory
            overwrite: force re-download
            timeout: cancel remaining requests if timeout exceeded (in seconds)
            fmt: download format - "json" or "csv"

        Returns:
            paths of output files
        """
        return self._download_resource(
            resource="structures",
            ids=ids,
            fmt=fmt,
            outdir=outdir,
            overwrite=overwrite,
            timeout=timeout,
        )

    def download_tables(
        self,
        ids: list[str],
        outdir: str | Path = MPCC_SETTINGS.DEFAULT_DOWNLOAD_DIR,
        overwrite: bool = False,
        timeout: int = -1,
        fmt: Literal["json", "csv"] = "json",
    ) -> list[Path]:
        """Download a list of tables as a .json.gz file.

        Args:
            ids: list of table ObjectIds
            outdir: optional output directory
            overwrite: force re-download
            timeout: cancel remaining requests if timeout exceeded (in seconds)
            fmt: download format - "json" or "csv"

        Returns:
            paths of output files
        """
        return self._download_resource(
            resource="tables",
            ids=ids,
            fmt=fmt,
            outdir=outdir,
            overwrite=overwrite,
            timeout=timeout,
        )

    def download_attachments(
        self,
        ids: list[str],
        outdir: str | Path = MPCC_SETTINGS.DEFAULT_DOWNLOAD_DIR,
        overwrite: bool = False,
        timeout: int = -1,
        fmt: Literal["json", "csv"] = "json",
    ) -> list[Path]:
        """Download a list of attachments as a .json.gz file.

        Args:
            ids: list of attachment ObjectIds
            outdir: optional output directory
            overwrite: force re-download
            timeout: cancel remaining requests if timeout exceeded (in seconds)
            fmt: download format - "json" or "csv"

        Returns:
            paths of output files
        """
        return self._download_resource(
            resource="attachments",
            ids=ids,
            fmt=fmt,
            outdir=outdir,
            overwrite=overwrite,
            timeout=timeout,
        )

    def _download_resource(
        self,
        resource: str,
        ids: list[str],
        outdir: str | Path = MPCC_SETTINGS.DEFAULT_DOWNLOAD_DIR,
        overwrite: bool = False,
        timeout: int = -1,
        fmt: Literal["json", "csv"] = "json",
    ) -> list[Path]:
        """Helper to download a list of resources as .json.gz file.

        Args:
            resource: type of resource
            ids: list of resource ObjectIds
            outdir: optional output directory
            overwrite: force re-download
            timeout: cancel remaining requests if timeout exceeded (in seconds)
            fmt: download format - "json" or "csv"

        Returns:
            list of paths to output files
        """
        resources = ["contributions"] + MPCC_SETTINGS.COMPONENTS
        if resource not in resources:
            raise MPContribsClientError(f"`resource` must be one of {resources}!")

        formats = {"json", "csv"}
        if fmt not in formats:
            raise MPContribsClientError(f"`fmt` must be one of {formats}!")

        oids = sorted(i for i in ids if ObjectId.is_valid(i))
        outdir = Path(outdir) or Path(".")
        subdir = outdir / resource
        subdir.mkdir(parents=True, exist_ok=True)
        model = self.get_model(f"{resource.capitalize()}Schema")
        fields = list(model._properties.keys())
        query: dict[str, str | list[str]] = {
            "format": fmt,
            "_fields": fields,
            "id__in": oids,
        }
        _, total_pages = self.get_totals(
            query=query, resource=resource, op="download", timeout=timeout
        )
        queries = self._split_query(
            query, resource=resource, op="download", pages=total_pages
        )
        paths: list[Path] = []
        futures: list[Any] = []

        for query in queries:
            digest = get_md5({"ids": query["id__in"].split(",")})  # type: ignore[union-attr]
            path = subdir / f"{digest}.{fmt}.gz"
            paths.append(path)

            if not path.exists() or overwrite:
                futures.append(
                    self._get_future(path, query, rel_url=f"{resource}/download/gz")
                )

        if futures:
            responses = _run_futures(futures, timeout=timeout)

            for p, resp in responses.items():
                Path(p).write_bytes(resp["result"])

        return paths
