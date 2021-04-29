from typing import List

from pydantic import BaseModel, Field, validator


class ImageEntry(BaseModel):
    """
    Model for an high resolution image entry in SurfacePropDoc
    """

    miller_index: List[int] = Field(
        None, description="Miller index of surface.",
    )

    image: bytes = Field(
        None, description="High resolution image data.",
    )

    # Make sure that the datetime field is properly formatted
    @validator("image", pre=True)
    def image_bytes_ok(cls, v):
        return str(v)


class WulffDoc(BaseModel):
    """
    Model for a document containing wulff construction image data.
    """

    hi_res_images: List[ImageEntry] = Field(
        None, description="List of individual surface image data.",
    )

    pretty_formula: str = Field(
        None, description="Reduced formula of the material.",
    )

    thumbnail: str = Field(
        None, description="Thumbnail image data.",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )

    # Make sure that the datetime field is properly formatted
    @validator("thumbnail", pre=True)
    def thumbnail_bytes_ok(cls, v):
        return str(v)
