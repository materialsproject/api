from enum import Enum


class ESCalcType(Enum):
    bandstructure = "bandstructure"
    dos = "dos"


class DOSProjection(Enum):
    total = "total"
    element = "element"
    orbital = "orbital"


class DOSDataFields(Enum):
    band_gap = "band_gap"
    cbm = "cbm"
    vbm = "vbm"


class SpinChannel(Enum):
    up = "1"
    down = "-1"

