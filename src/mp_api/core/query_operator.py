from typing import List, Dict, Optional
from pydantic import BaseModel
from fastapi import Query
from monty.json import MSONable
from mp_api.core.utils import STORE_PARAMS, dynamic_import


class QueryOperator(MSONable):
    """
    Base Query Operator class for defining powerfull query language
    in the Materials API
    """

    def query(self) -> STORE_PARAMS:
        """
        The query function that does the work for this query operator
        """
        raise NotImplementedError("Query operators must implement query")

    def post_process(self):
        """
        An optional post-processing function for the data
        """
        pass


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
            if limit > max_limit:
                raise Exception(
                    "Requested more data per query than allowed by this endpoint."
                    f"The max limit is {max_limit} entries"
                )
            return {"skip": skip, "limit": limit}

        self.query = query


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

        if isinstance(model, str):
            module_path = ".".join(model.split(".")[:-1])
            class_name = model.split(".")[-1]
            self.model = dynamic_import(module_path, class_name)
            assert issubclass(
                self.model, BaseModel
            ), "The resource model has to be a PyDantic Model"
        else:
            self.model = model

        model_fields = list(self.model.__fields__.keys())

        self.default_fields = (
            model_fields if default_fields is None else list(default_fields)
        )
        assert set(self.default_fields).issubset(
            model_fields
        ), "default projection contains some fields that are not in the model fields"

        default_fields_string = ",".join(default_fields)

        def query(
            fields: str = Query(
                default_fields_string,
                description=f"Fields to project from {model.__name__} as a list of comma seperated strings",
            ),
            all_fields: bool = Query(False, description="Include all fields."),
        ) -> STORE_PARAMS:
            """
            Pagination parameters for the API Endpoint
            """

            fields = fields.split(",")
            if all_fields:
                fields = model_fields

            return {"properties": fields}

        self.query = query

    def as_dict(self) -> Dict:
        """
        Special as_dict implemented to convert pydantic models into strings
        """

        d = super().as_dict()  # Ensures sub-classes serialize correctly
        d["model"] = f"{self.model.__module__}.{self.model.__name__}"
        return d
