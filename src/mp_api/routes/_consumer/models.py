from pydantic import BaseModel, Field


class UserSettingsDoc(BaseModel):
    """
    Defines data for user settings
    """

    consumer_id: str = Field(
        None, title="Consumer ID", description="Consumer ID for a specific user."
    )

    settings: dict = Field(
        None,
        title="Consumer ID settings",
        description="Settings defined for a specific user.",
    )
