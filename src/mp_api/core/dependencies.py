from pydantic import BaseModel
from typing import List, Optional, Union, Any, Dict, Callable
from typing_extensions import Literal
from fastapi import Query


STORE_PARAMS = Dict[Literal["criteria", "properties", "skip", "limit"], Any]


def pagination_params_factory(
    default_skip: int = 0, default_limit: int = 10, max_limit: int = 100
) -> Callable[..., STORE_PARAMS]:
    """
    Factory method to generate a dependency for pagination in FastAPI

    Args:
        default_skip: default number of items to skip
        default_limit: default number of items to return
        max_limit: max number of items to return
    """

    def paginate(
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

    return paginate


def fieldset_params_factory(
    model: BaseModel, default_fields: Union[None, str, List[str]] = None
) -> Callable[..., STORE_PARAMS]:
    """
    Factory method to generate a dependency for sparse field sets in FastAPI

    Args:
        model: PyDantic Model that represents the underlying data source
        default_fields: default fields to return in the API response if no fields are explicitly requested
        ignored_fields: fields to i
    """

    default_fields = ",".join(default_fields) if default_fields else None
    projection_type = Optional[str] if default_fields is None else str
    all_model_fields = list(model.__fields__.keys())

    def field_set(
        fields: projection_type = Query(
            default_fields,
            description=f"Fields to project from {model.__name__} as a list of comma seperated strings",
        ),
        all_fields: bool = Query(False, description="Include all fields."),
    ) -> STORE_PARAMS:
        """
        Pagination parameters for the API Endpoint
        """
        all_fields = all_fields

        fields = fields.split(",") if isinstance(fields, str) else None

        if fields is not None and all_fields:
            raise Exception("projection and all_includes does not match")
        elif all_fields:
            fields = all_model_fields

        return {"properties": fields}

    return field_set
