from typing import List, Dict, Union, Optional, Callable, Type
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from monty.json import MSONable
from fastapi import FastAPI, APIRouter, Path, HTTPException, Depends, Query, Request
from fastapi.routing import APIRoute
from inspect import signature

from maggma.core import Store

from mp_api.core.models import Response
from mp_api.core.utils import (
    STORE_PARAMS,
    merge_queries,
    attach_signature,
    dynamic_import,
)
from mp_api.core.query_operator import (
    QueryOperator,
    PaginationQuery,
    SparseFieldsQuery,
    VersionQuery,
)


class Resource(MSONable):
    """
    Implements a REST Compatible Resource as a URL endpoint
    This class provides a number of convenience features
    including full pagination, field projection, and the
    MAPI query lanaugage

    - implements custom error handlers to provide MAPI Responses
    - implement standard metadata respomse for class
    - JSON Configuration
    """

    def __init__(
        self,
        store: Store,
        model: Union[BaseModel, str],
        tags: Optional[List[str]] = None,
        query_operators: Optional[List[QueryOperator]] = None,
        route_class: Type[APIRoute] = None,
        key_fields: List[str] = None,
        custom_endpoint_funcs: List[Callable] = None,
        enable_get_by_key: bool = True,
        enable_default_search: bool = True,
    ):
        """
        Args:
            store: The Maggma Store to get data from
            model: the pydantic model to apply to the documents from the Store
                This can be a string with a full python path to a model or
                an actuall pydantic Model if this is being instantied in python
                code. Serializing this via Monty will autoconvert the pydantic model
                into a python path string
            tags: list of tags for the Endpoint
            query_operators: operators for the query language
            route_class: Custom APIRoute class to define post-processing or custom validation
                of response data
            key_fields: List of fields to always project. Default uses SparseFieldsQuery
                to allow user's to define these on-the-fly.
            custom_endpoint_funcs: Custom endpoint preparation functions to be used
            enable_get_by_key: Enable default key route for endpoint.
            enable_default_search: Enable default endpoint search behavior.
        """
        self.store = store
        self.tags = tags or []
        self.key_fields = key_fields
        self.versioned = False
        self.cep = custom_endpoint_funcs
        self.enable_get_by_key = enable_get_by_key
        self.enable_default_search = enable_default_search

        if isinstance(model, str):
            module_path = ".".join(model.split(".")[:-1])
            class_name = model.split(".")[-1]
            class_model = dynamic_import(module_path, class_name)
            assert issubclass(
                class_model, BaseModel
            ), "The resource model has to be a PyDantic Model"
            self.model = class_model
        elif isinstance(model, type) and issubclass(model, BaseModel):
            self.model = model
        else:
            raise ValueError("The resource model has to be a PyDantic Model")

        self.query_operators = (
            query_operators
            if query_operators is not None
            else [
                PaginationQuery(),
                SparseFieldsQuery(
                    self.model,
                    default_fields=[self.store.key, self.store.last_updated_field],
                ),
            ]
        )

        if any(
            isinstance(qop_entry, VersionQuery) for qop_entry in self.query_operators
        ):
            self.versioned = True

        if route_class is not None:
            self.router = APIRouter(route_class=route_class)
        else:
            self.router = APIRouter()
        self.response_model = Response[self.model]  # type: ignore
        self.prepare_endpoint()

    def prepare_endpoint(self):
        """
        Internal method to prepare the endpoint by setting up default handlers
        for routes
        """

        if self.cep is not None:
            for func in self.cep:
                func(self)

        if self.enable_get_by_key:
            self.build_get_by_key()

        if self.enable_default_search:
            self.set_dynamic_model_search()

    def build_get_by_key(self):
        key_name = self.store.key
        model_name = self.model.__name__

        if self.key_fields is None:
            field_input = SparseFieldsQuery(
                self.model, [self.store.key, self.store.last_updated_field]
            ).query
        else:

            def field_input():
                return {"properties": self.key_fields}

        if not self.versioned:

            async def get_by_key(
                key: str = Path(
                    ...,
                    alias=key_name,
                    title=f"The {key_name} of the {model_name} to get",
                ),
                fields: STORE_PARAMS = Depends(field_input),
            ):
                f"""
                Get's a document by the primary key in the store

                Args:
                    {key_name}: the id of a single {model_name}

                Returns:
                    a single {model_name} document
                """
                self.store.connect()

                item = self.store.query_one(
                    criteria={self.store.key: key}, properties=fields["properties"]
                )

                if item is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item with {self.store.key} = {key} not found",
                    )

                response = {"data": [item]}

                return response

            self.router.get(
                f"/{{{key_name}}}/",
                response_description=f"Get an {model_name} by {key_name}",
                response_model=self.response_model,
                response_model_exclude_unset=True,
                tags=self.tags,
            )(get_by_key)

        else:

            async def get_by_key_versioned(
                key: str = Path(
                    ...,
                    alias=key_name,
                    title=f"The {key_name} of the {model_name} to get",
                ),
                fields: STORE_PARAMS = Depends(field_input),
                version: str = Query(
                    None,
                    description="Database version to query on formatted as YYYY.MM.DD",
                ),
            ):
                f"""
                Get's a document by the primary key in the store

                Args:
                    {key_name}: the id of a single {model_name}

                Returns:
                    a single {model_name} document
                """

                if version is not None:
                    version = version.replace(".", "_")
                    self.store.collection_name = (
                        f"{self.store.collection_name}_{version}"
                    )
                self.store.connect()

                item = self.store.query_one(
                    criteria={self.store.key: key}, properties=fields["properties"]
                )

                if item is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item with {self.store.key} = {key} not found",
                    )

                response = {"data": [item]}

                return response

            self.router.get(
                f"/{{{key_name}}}/",
                response_description=f"Get an {model_name} by {key_name}",
                response_model=self.response_model,
                response_model_exclude_unset=True,
                tags=self.tags,
            )(get_by_key_versioned)

    def set_dynamic_model_search(self):

        model_name = self.model.__name__

        async def search(**queries: STORE_PARAMS):

            request = queries.pop("request")  # type: ignore

            query: STORE_PARAMS = merge_queries(list(queries.values()))

            query_params = [
                entry
                for _, i in enumerate(self.query_operators)
                for entry in signature(i.query).parameters
            ]

            overlap = [
                key for key in request.query_params.keys() if key not in query_params
            ]
            if any(overlap):
                raise HTTPException(
                    status_code=404,
                    detail="Request contains query parameters which cannot be used: {}".format(
                        ", ".join(overlap)
                    ),
                )

            if self.versioned and query["criteria"].get("version", None) is not None:
                version = query["criteria"]["version"].replace(".", "_")
                self.store.collection_name = f"{self.store.collection_name}_{version}"
                query["criteria"].pop("version")

            self.store.connect()

            data = list(self.store.query(**query))  # type: ignore
            operator_metas = [
                operator.meta(self.store, query.get("criteria", {}))
                for operator in self.query_operators
            ]
            meta = {k: v for m in operator_metas for k, v in m.items()}

            response = {"data": data, "meta": meta}

            return response

        ann = {f"dep{i}": STORE_PARAMS for i, _ in enumerate(self.query_operators)}
        ann.update({"request": Request})
        attach_signature(
            search,
            annotations=ann,
            defaults={
                f"dep{i}": Depends(dep.query)
                for i, dep in enumerate(self.query_operators)
            },
        )

        self.router.get(
            "/",
            tags=self.tags,
            summary=f"Get {model_name} documents",
            response_model=self.response_model,
            response_description=f"Search for a {model_name}",
            response_model_exclude_unset=True,
        )(search)

        @self.router.get("", include_in_schema=False)
        def redirect_unslashes():
            """
            Redirects unforward slashed url to resource
            url with the forward slash
            """

            url = self.router.url_path_for("/")
            return RedirectResponse(url=url, status_code=301)

    def run(self):  # pragma: no cover
        """
        Runs the Endpoint cluster locally
        This is intended for testing not production
        """
        import uvicorn

        app = FastAPI()
        app.include_router(self.router, prefix="")
        uvicorn.run(app)

    def as_dict(self) -> Dict:
        """
        Special as_dict implemented to convert pydantic models into strings
        """

        d = super().as_dict()  # Ensures sub-classes serialize correctly
        d["model"] = f"{self.model.__module__}.{self.model.__name__}"
        return d
