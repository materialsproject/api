from typing import Dict, Union
from pydantic import BaseModel, Field
from emmet.core.mpid import MPID
from datetime import datetime
from pymatgen.electronic_structure.bandstructure import BandStructureSymmLine
from pymatgen.electronic_structure.dos import CompleteDos


class BSObjectDoc(BaseModel):
    """
    Band object document.
    """

    task_id: MPID = Field(
        None, description="The calculation ID this property comes from"
    )

    last_updated: datetime = Field(
        description="The timestamp when this calculation was last updated",
        default_factory=datetime.utcnow,
    )

    data: Union[Dict, BandStructureSymmLine] = Field(
        None, description="The band structure object for the given calculation ID"
    )


class DOSObjectDoc(BaseModel):
    """
    DOS object document.
    """

    task_id: MPID = Field(
        None, description="The calculation ID this property comes from"
    )

    last_updated: datetime = Field(
        description="The timestamp when this calculation was last updated",
        default_factory=datetime.utcnow,
    )

    data: CompleteDos = Field(
        None, description="The density of states object for the given calculation ID"
    )
