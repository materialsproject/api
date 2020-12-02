from pydantic import BaseModel, Field


class MoleculesDoc(BaseModel):
    """
    Model for a document containing molecule data
    """

    nelements: int = Field(
        None,
        description="Number of elements in the molecule.",
    )

    EA: float = Field(
        None,
        description="Electron affinity of the molecule in eV.",
    )

    IE: float = Field(
        None,
        description="Ionization energy of the molecule in eV.",
    )

    charge: int = Field(
        None,
        description="Charge of the molecule in +e.",
    )

    pointgroup: str = Field(
        None,
        description="Point group of the molecule in Schoenflies notation.",
    )

    smiles: str = Field(
        None,
        description="The simplified molecular input line-entry system (SMILES) \
            representation of the molecule.",
    )

    task_id: str = Field(
        None,
        description="Materials Project molecule ID. This takes the form mol-*****",
    )

    molecule: dict = Field(
        None,
        description="Pymatgen molecule object.",
    )

    pretty_formula: str = Field(
        None,
        description="Chemical formula of the molecule.",
    )

    svg: str = Field(
        None,
        description="String representation of the SVG image of the molecule.",
    )
