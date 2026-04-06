"""Define unit registry used in the client."""
from __future__ import annotations

from pint import UnitRegistry

custom_units = """#
ppb = 1e-9
atom = 1
electron_mass = 9.1093837015e-31 kg = mₑ = m_e
sccm = cm³/min
"""

ureg: UnitRegistry = UnitRegistry(
    autoconvert_offset_to_baseunit=True,
    preprocessors=[
        lambda s: s.replace("%%", " permille "),
        lambda s: s.replace("%", " percent "),
    ],
)
ureg.load_definitions(custom_units.splitlines())
