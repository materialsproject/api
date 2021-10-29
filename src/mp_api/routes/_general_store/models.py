from pydantic import BaseModel, Field
from typing import Dict

try:
    from typing import Literal  # type: ignore
except ImportError:
    from typing_extensions import Literal
from datetime import datetime


class GeneralStoreDoc(BaseModel):
    """
    Defines general store data
    """

    kind: Literal["newsfeed", "seminar", "banner"] = Field(
        None, description="Type of the data."
    )

    markdown: str = Field(None, description="Markdown data.")

    meta: Dict = Field(None, description="Metadata.")

    last_updated: datetime = Field(
        description="Timestamp for when this document was last updated",
        default_factory=datetime.utcnow,
    )
