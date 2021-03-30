from typing import List, Dict, Optional
from pydantic import BaseModel
from fastapi import Query, HTTPException
from monty.json import MSONable
from maggma.core import Store
from mp_api.core.utils import STORE_PARAMS, dynamic_import


class QueryOperator(MSONable):
    """
    Base Query Operator class for defining powerful query language
    in the Materials API
    """

    def query(self) -> STORE_PARAMS:
        """
        The query function that does the work for this query operator
        """
        raise NotImplementedError("Query operators must implement query")

    def meta(self, store: Store, query: Dict) -> Dict:
        """
        Returns meta data to return with the Response

        Args:
            store: the Maggma Store that the resource uses
            query: the query being executed in this API call
        """
        return {}

    def post_process(self, docs: List[Dict]) -> List[Dict]:
        """
        An optional post-processing function for the data
        """
        return docs


class PaginationQuery(QueryOperator):
    """Query opertators to provides Pagination in the Materials API"""

    def __init__(
        self, default_skip: int = 0, default_limit: int = 10, max_limit: int = 100
    ):
        """
        Args:
            default_skip: the default number of documents to skip
            default_limit: the default number of documents to return
            max_limit: max number of documents to return
        """
        self.default_skip = default_skip
        self.default_limit = default_limit
        self.max_limit = max_limit

        def query(
            skip: int = Query(
                default_skip, description="Number of entries to skip in the search"
            ),
            limit: int = Query(
                default_limit,
                description="Max number of entries to return in a single query."
                f" Limited to {max_limit}",
            ),
        ) -> STORE_PARAMS:
            """
            Pagination parameters for the API Endpoint
            """
            if limit <= 0 or limit > max_limit:
                limit = max_limit
            return {"skip": skip, "limit": limit}

        setattr(self, "query", query)

    def meta(self, store: Store, query: Dict) -> Dict:
        """
        Metadata for the pagination params

        Args:
            store: the Maggma Store that the resource uses
            query: the query being executed in this API call
        """

        count = store.count(query)
        return {"max_limit": self.max_limit, "total": count}


class SparseFieldsQuery(QueryOperator):
    """
    Factory function to generate a dependency for sparse field sets in FastAPI
    """

    def __init__(self, model: BaseModel, default_fields: Optional[List[str]] = None):
        """
        Args:
            model: PyDantic Model that represents the underlying data source
            default_fields: default fields to return in the API response if no fields are explicitly requested
        """

        self.model = model

        model_name = self.model.__name__  # type: ignore
        model_fields = list(self.model.__fields__.keys())

        self.default_fields = (
            model_fields if default_fields is None else list(default_fields)
        )

        def query(
            fields: str = Query(
                None,
                description=f"Fields to project from {str(model_name)} as a list of comma seperated strings",
            ),
            all_fields: bool = Query(False, description="Include all fields."),
        ) -> STORE_PARAMS:
            """
            Pagination parameters for the API Endpoint
            """

            properties = (
                fields.split(",") if isinstance(fields, str) else self.default_fields
            )
            if all_fields:
                properties = model_fields

            return {"properties": properties}

        setattr(self, "query", query)

    def meta(self, store: Store, query: Dict) -> Dict:
        """
        Returns metadata for the Sparse field set

        Args:
            store: the Maggma Store that the resource uses
            query: the query being executed in this API call
        """
        return {"default_fields": self.default_fields}

    def as_dict(self) -> Dict:
        """
        Special as_dict implemented to convert pydantic models into strings
        """

        d = super().as_dict()  # Ensures sub-classes serialize correctly
        d["model"] = f"{self.model.__module__}.{self.model.__name__}"  # type: ignore
        return d

    @classmethod
    def from_dict(cls, d):

        model = d.get("model")
        if isinstance(model, str):
            module_path = ".".join(model.split(".")[:-1])
            class_name = model.split(".")[-1]
            model = dynamic_import(module_path, class_name)

        assert issubclass(
            model, BaseModel
        ), "The resource model has to be a PyDantic Model"
        d["model"] = model

        return cls(**d)


class VersionQuery(QueryOperator):
    """
    Method to generate a query on a specific collection version
    """

    def query(
        self,
        version: Optional[str] = Query(
            None, description="Database version to query on formatted as YYYY.MM.DD",
        ),
    ) -> STORE_PARAMS:

        crit = {}

        if version:
            crit.update({"version": version})

        return {"criteria": crit}


class SortQuery(QueryOperator):
    """
    Method to generate the sorting portion of a query
    """

    def query(
        self,
        field: Optional[str] = Query(None, description="Field to sort with"),
        ascending: Optional[bool] = Query(
            None, description="Whether the sorting should be ascending",
        ),
    ) -> STORE_PARAMS:

        sort = {}

        if field and ascending is not None:
            sort.update({field: 1 if ascending else -1})

        elif field or ascending is not None:
            raise HTTPException(
                status_code=404,
                detail="Must specify both a field and order for sorting.",
            )

        return {"sort": sort}
