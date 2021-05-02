from pydantic import BaseModel, Field


class DOIDoc(BaseModel):
    """
    DOIs to reference specific materials on Materials Project.
    """

    doi: str = Field(
        None,
        description="DOI of the material.",
    )

    bibtex: str = Field(
        None,
        description="Bibtex reference of the material.",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )
