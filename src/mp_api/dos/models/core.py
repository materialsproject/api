from typing import Dict, List, Union
from enum import Enum

from pydantic import BaseModel, Field, validator


class ESCalcType(Enum):
    bandstructure = "bandstructure"
    dos = "dos"


class DOSProjection(Enum):
    total = "total"
    elements = "elements"
    orbitals = "orbitals"


class SpinChannel(Enum):
    spin_up = "1"
    spin_down = "-1"


class OrbitalType(Enum):
    s = "s"
    p = "p"
    d = "d"
    f = "f"

