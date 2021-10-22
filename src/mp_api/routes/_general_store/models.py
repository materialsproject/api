from pydantic import BaseModel, Field
from datetime import datetime


class GeneralStoreDoc(BaseModel):
    """
    Defines general store data
    """

    kind: str = Field(None, description="Type of the data.")

    markdown: str = Field(None, description="Markdown data.")

    meta: str = Field(None, description="Metadata.")

    last_updated: datetime = Field(
        description="Timestamp for when this document was last updated",
        default_factory=datetime.utcnow,
    )
