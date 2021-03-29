from pydantic import BaseModel, Field


class UserSettingsDoc(BaseModel):
    """
    Defines data for user settings
    """

    consumer_id: str = Field(
        None, title="Consumer ID", description="Consumer ID for a specific user."
    )

    successful: bool = Field(
        None,
        title="Successful Write",
        description="Whether the user settings were written successfully.",
    )

