"""Test the oxygen evolution analysis features in the client."""

import json
import pytest
import numpy as np
from scipy.interpolate import splev

from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.core import Composition
from pymatgen.entries.computed_entries import ComputedEntry

from mp_api.client.core._oxygen_evolution import (
    DEFAULT_CACHE_FILE,
    NIST_JANAF_O2_MU_T,
    OxygenEvolution,
)


def test_interp():
    oxyevo = OxygenEvolution()

    # Spline interpolation is exact for all fit points:
    assert np.allclose(
        oxyevo.mu_to_temp_spline(np.array(NIST_JANAF_O2_MU_T["mu-mu_0K"])),
        NIST_JANAF_O2_MU_T["temperature"],
    )

    # mu(T) is a generally decreasing function, at least for fit range
    deriv = splev(
        np.linspace(
            min(NIST_JANAF_O2_MU_T["mu-mu_0K"]),
            max(NIST_JANAF_O2_MU_T["mu-mu_0K"]),
            1000,
        ),
        oxyevo.mu_to_temp_spline_params(),
        der=1,
    )
    assert len(deriv[deriv > 0]) == 0

    # ensure user is warned when data is outside fit range
    for badval in (1.0, -50.0):
        with pytest.warns(UserWarning, match="outside the fitting range"):
            oxyevo.mu_to_temp_spline(badval)


def test_get():
    """Test data retrieval from NIST."""

    data = {}
    data["temperature"], data["mu-mu_0K"] = OxygenEvolution().get_chempot_temp_data()
    assert DEFAULT_CACHE_FILE.exists()
    assert all(np.allclose(data[k], v) for k, v in NIST_JANAF_O2_MU_T.items())
    json_data = json.loads(DEFAULT_CACHE_FILE.read_text())
    assert all(np.allclose(json_data[k], v) for k, v in NIST_JANAF_O2_MU_T.items())


def test_oxy_evo():
    """Very fake Al-O chemical system for testing purposes."""
    entries = [
        ComputedEntry({"Al": 1}, -2.0),
        ComputedEntry({"O": 1}, -5.0),
        ComputedEntry({"Al": 1, "O": 1}, -25.0),
        ComputedEntry({"Al": 2, "O": 3}, -55.0),
        ComputedEntry({"Al": 3, "O": 2}, -5.0),
    ]
    phase_diag = PhaseDiagram(entries)

    ref_comp = Composition({"Al": 4, "O": 1})
    evo = OxygenEvolution().get_oxygen_evolution_from_phase_diagram(
        phase_diag, [ref_comp]
    )
    assert ref_comp.formula in evo
    assert np.allclose(evo[ref_comp.formula]["evolution"], [0.5, 0.5, -1.5])
    assert np.allclose(evo[ref_comp.formula]["temperature"], [5949.70500942, 0.0, 0.0])
    assert all(
        str(evo[ref_comp.formula]["reaction"][idx]) == rxn
        for idx, rxn in enumerate(
            [
                "2 Al4O -> 8 Al + O2",
                "2 Al4O -> 8 Al + O2",
                "2 Al4O + 3 O2 -> 8 AlO",
            ]
        )
    )
