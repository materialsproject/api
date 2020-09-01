from typing import List, Dict, Union, Optional
from starlette.responses import RedirectResponse
from pydantic import BaseModel
from monty.json import MSONable
from fastapi import FastAPI, APIRouter, Path, HTTPException, Depends
from fastapi.routing import APIRoute

from maggma.core import Store

from mp_api.core.models import Response
from mp_api.core.utils import (
    STORE_PARAMS,
    merge_queries,
    attach_signature,
    dynamic_import,
)
from mp_api.core.query_operator import QueryOperator, PaginationQuery, SparseFieldsQuery


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
        route_class: APIRoute = None,
        key_fields: List[str] = [None],
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
        """
        self.store = store
        self.tags = tags or []
        self.key_fields = key_fields

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

        self.build_get_by_key()
        self.set_dynamic_model_search()

    def build_get_by_key(self):
        key_name = self.store.key
        model_name = self.model.__name__

        if None in self.key_fields:
            field_input = SparseFieldsQuery(
                self.model, [self.store.key, self.store.last_updated_field]
            ).query
        else:
            field_input = lambda: {"properties": self.key_fields}

        async def get_by_key(
            key: str = Path(
                ..., alias=key_name, title=f"The {key_name} of the {model_name} to get"
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

    def set_dynamic_model_search(self):

        model_name = self.model.__name__

        async def search(**queries: STORE_PARAMS):
            self.store.connect()

            query: STORE_PARAMS = merge_queries(list(queries.values()))
            data = list(self.store.query(**query))  # type: ignore
            operator_metas = [
                operator.meta(self.store, query.get("criteria", {}))
                for operator in self.query_operators
            ]
            meta = {k: v for m in operator_metas for k, v in m.items()}

            response = {"data": data, "meta": meta}

            return response

        attach_signature(
            search,
            annotations={
                f"dep{i}": STORE_PARAMS for i, _ in enumerate(self.query_operators)
            },
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
