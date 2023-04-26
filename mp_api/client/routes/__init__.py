try:
    from .alloys import AlloysRester
except ImportError:
    AlloysRester = None  # type: ignore

try:
    from .charge_density import ChargeDensityRester
except ImportError:
    ChargeDensityRester = None  # type: ignore
