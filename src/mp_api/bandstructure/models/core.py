from enum import Enum


class ESCalcType(Enum):
    bandstructure = "bandstructure"
    dos = "dos"


class BSPathType(Enum):
    sc = "Setyawan-Curtarolo"
    hin = "Hinuma et al."
    lm = "Latimer-Munro"


class BSDataFields(Enum):
    band_gap = "band_gap"
    cbm = "cbm"
    vbm = "vbm"
