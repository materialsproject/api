from typing import List
from pydantic import BaseModel, Field
from pymatgen.core.periodic_table import Element
from pymatgen.core.structure import Molecule


class MoleculesDoc(BaseModel):
    """
    Molecules relevant to battery electrolytes.
    """

    elements: List[Element] = Field(
        None, description="List of elements in the molecule.",
    )

    nelements: int = Field(
        None, description="Number of elements in the molecule.",
    )

    EA: float = Field(
        None, description="Electron affinity of the molecule in eV.",
    )

    IE: float = Field(
        None, description="Ionization energy of the molecule in eV.",
    )

    charge: int = Field(
        None, description="Charge of the molecule in +e.",
    )

    pointgroup: str = Field(
        None, description="Point group of the molecule in Schoenflies notation.",
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

    molecule: Molecule = Field(
        None, description="Pymatgen molecule object.",
    )

    formula_pretty: str = Field(
        None, description="Chemical formula of the molecule.",
    )

    svg: str = Field(
        None, description="String representation of the SVG image of the molecule.",
    )
