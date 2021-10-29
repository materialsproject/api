from pydantic import BaseModel, Field
from typing import Dict, Literal
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
