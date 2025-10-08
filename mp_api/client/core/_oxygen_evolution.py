"""Compute the oxygen evolution of a phase."""

from __future__ import annotations

import json
from collections.abc import Sequence
from io import StringIO
from pathlib import Path
from warnings import warn

import numpy as np
import pandas as pd
import requests
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.core import Composition, Element
from scipy.constants import Avogadro, Boltzmann, atm, elementary_charge
from scipy.interpolate import make_splrep, splev

DEFAULT_CACHE_FILE = Path(__file__).absolute().parent / "JANAF_O2_data.json"
# O2 partial pressure at ambient conditions, in MPa
O2_PARTIAL_PRESSURE = 0.21 * atm * 1e-6


class OxygenEvolution:
    """Compute the oxygen evolution using experimental data and atomistic phase diagrams.

    Parameters
    -----------
    cache_file : Path or None
        If a Path, the path to the file at which NIST JANAF data is cached / retrieved.
        If None, no caching is performed.
    """

    def __init__(
        self,
        cache_file: Path = DEFAULT_CACHE_FILE,
    ):
        self._spline_pars = None
        self.cache_file = cache_file

    def get_chempot_temp_data(
        self,
        nist_url: str = "https://janaf.nist.gov/tables/O-029.txt",
        ref_p: float = O2_PARTIAL_PRESSURE,
        meas_p: float = 0.1,  # The reference pressure reported in JANAF, 0.1 MPa
    ) -> tuple[np.ndarray, np.ndarray]:
        """Get the approximate relationship between the O2 chemical potential and temperature.

        The user is advised not to change the default parameters below unless they
        know what they control.

        Parameters
        -----------
        nist_url : str
            The link to the txt / TSV data on NIST's JANAF tables for gaseous O2
        ref_p : float
            The reference pressure for O2 at ambient conditions.
            The default value is 0.21 atmospheres, which we convert to MPa
        meas_p : float
            The O2 partial pressure at which the experimental data was collected.
            Per NIST, this is 0.1 MPa

        Returns:
        -----------
        tuple of
            Temperature in K (np.ndarray)
            O2 chemical potential in eV/atom (np.ndarray)
        """
        if self.cache_file and self.cache_file.exists():
            data = json.loads(self.cache_file.read_text())
            return tuple(np.array(data[k]) for k in ("temperature", "mu-mu_0K"))  # type: ignore

        response = requests.get(nist_url)

        with StringIO(initial_value=response.content.decode()) as stio:
            janaf_data = pd.read_csv(stio, sep="\t", header=1)

        kB_eV = Boltzmann / elementary_charge

        temp_K = janaf_data["T(K)"].to_numpy()
        entropy_dimless = janaf_data["S"].to_numpy() / (Boltzmann * Avogadro)

        # Note that the ideal gas contribution to the chemical potential is
        # (Gibbs-Helmholtz relation)
        # G(p, T)/N = G(p_0, T_0)/N + k_B T ln(p/p_0)
        # where  G(p_0, T_0)/N is a reference chemical potential for the system
        # We use the zero temperature energy per atom to approximate this later
        mu_mu0 = kB_eV * temp_K * (1.0 + np.log(meas_p / ref_p) - entropy_dimless)
        if self.cache_file:
            self.cache_file.write_text(
                json.dumps(
                    {"mu-mu_0K": mu_mu0.tolist(), "temperature": temp_K.tolist()},
                )
            )

        return temp_K, mu_mu0

    def mu_to_temp_spline_params(self):
        if self._spline_pars is None:
            temp = np.array(NIST_JANAF_O2_MU_T["temperature"])
            mu_m0 = np.array(NIST_JANAF_O2_MU_T["mu-mu_0K"])
            # spline needs the x vars to be in increasing order
            mu_sort_idx = np.argsort(mu_m0)
            self._spline_pars = make_splrep(mu_m0[mu_sort_idx], temp[mu_sort_idx])
        return self._spline_pars

    def mu_to_temp_spline(
        self,
        mu: Sequence[float],
    ):
        """Interpolate the O2 chemical potential vs. T relationship.

        Parameters
        -----------
        mu : np.ndarray
            The O2 chemical potentials to sample at.
        """
        mu_arr = np.array(mu)
        if np.any(
            (mu_arr < min(NIST_JANAF_O2_MU_T["mu-mu_0K"]))
            | (mu_arr > max(NIST_JANAF_O2_MU_T["mu-mu_0K"]))
        ):
            warn(
                "Some of the input chemical potential values are "
                "outside the fitting range - extrapolation will be inaccurate.",
                stacklevel=2,
            )
        return splev(mu_arr, self.mu_to_temp_spline_params())

    @staticmethod
    def stairstep(x, y, z):
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)
        isort = np.argsort(x)

        new_x = np.zeros(2 * x.shape[0] - 1)
        new_y = np.zeros(2 * y.shape[0] - 1)
        new_z = np.zeros(2 * z.shape[0] - 1, dtype=object)

        new_x[::2] = x[isort]
        new_x[1::2] = x[isort][1:]

        new_y[::2] = y[isort]
        new_y[1::2] = y[isort][:-1]

        new_z[::2] = z[isort]
        new_z[1::2] = z[isort][:-1]

        return new_x, new_y, new_z

    def get_oxygen_evolution_from_phase_diagram(
        self,
        phase_diagram: PhaseDiagram,
        compositions: list[Composition] | set[Composition],
    ) -> dict[str, np.ndarray]:
        by_dict = {
            composition.formula: [
                {
                    k: profile[v]
                    for k, v in {
                        "mu": "chempot",
                        "reaction": "reaction",
                        "evolution": "evolution",
                    }.items()
                }
                for profile in phase_diagram.get_element_profile("O", composition)
            ]
            for composition in set(compositions)
        }

        for formula, data in by_dict.items():
            for idx, entry in enumerate(data):
                # Normalize all reactions to have integer coefficients
                scale = entry["reaction"].normalized_repr_and_factor()[1]
                by_dict[formula][idx]["reaction"]._coeffs = [
                    c * scale for c in entry["reaction"]._coeffs
                ]

        oxy_evo_data: dict = {
            formula: {
                k: [data[idx][k] for idx in range(len(data))]
                for k in (
                    "mu",
                    "reaction",
                    "evolution",
                )
            }
            for formula, data in by_dict.items()
        }

        mu_0K = phase_diagram.el_refs[Element.O].energy_per_atom

        for formula, data in oxy_evo_data.items():
            (
                oxy_evo_data[formula]["mu"],
                oxy_evo_data[formula]["evolution"],
                oxy_evo_data[formula]["reaction"],
            ) = self.stairstep(*(data[k] for k in ("mu", "evolution", "reaction")))
            # This is the normalization convention we adopt for MP
            oxy_evo_data[formula]["evolution"] *= -0.5
            oxy_evo_data[formula]["temperature"] = self.mu_to_temp_spline(
                data["mu"] - mu_0K
            )
        return oxy_evo_data


# This data is generated by running:
# `OxygenEvolution().get_chempot_temp_data()`
# The contents of `DEFAULT_CACHE_FILE` will contain this data.
# Because the last update of the JANAF tables was in 1998
# (writing in 2025), we see no need to dynamically retrieve this data
NIST_JANAF_O2_MU_T = {
    "mu-mu_0K": [
        0.0,
        -0.15766752295964667,
        -0.35716109254410505,
        -0.4633062592086276,
        -0.5684747265209704,
        -0.5725679617587883,
        -0.6845046823072302,
        -0.7988365855732343,
        -0.9153600136580551,
        -1.0338982557640533,
        -1.2764843857253183,
        -1.5256155519745132,
        -1.7804988878829335,
        -2.0404658980577506,
        -2.304982822611666,
        -2.5736050343764276,
        -2.8459749660488933,
        -3.1217816895393757,
        -3.4007764623761245,
        -3.6827416348963578,
        -3.9674927231001944,
        -4.254892918628172,
        -4.544805413120827,
        -4.837112053904078,
        -5.13170297971957,
        -5.428488021421295,
        -5.7273687184475115,
        -6.028299468011739,
        -6.3311932102488635,
        -6.635957703158943,
        -6.9425981288768055,
        -7.2509807883238855,
        -7.561092207949628,
        -7.872879529978791,
        -8.186271240950743,
        -8.501236248056516,
        -8.817722729947826,
        -9.135721358781987,
        -9.4551295282894,
        -9.775953457031855,
        -10.098137177953216,
        -10.421667217502918,
        -10.746499009321454,
        -11.072592132757157,
        -11.399910312866226,
        -11.728421420412731,
        -12.058141001801161,
        -12.389003762132672,
        -12.720990009294923,
        -13.05408419688343,
        -13.388322599841986,
        -13.723603648327966,
        -14.059921123779567,
        -14.397323738264184,
        -14.735764852568353,
        -15.075250685253877,
        -15.415683812185982,
        -15.757182386038748,
        -16.099653128385278,
        -16.44311262205701,
        -16.787639635503336,
        -17.13308492324121,
        -17.47953139942788,
        -17.826947971254377,
        -18.175365731529666,
    ],
    "temperature": [
        0.0,
        100.0,
        200.0,
        250.0,
        298.15,
        300.0,
        350.0,
        400.0,
        450.0,
        500.0,
        600.0,
        700.0,
        800.0,
        900.0,
        1000.0,
        1100.0,
        1200.0,
        1300.0,
        1400.0,
        1500.0,
        1600.0,
        1700.0,
        1800.0,
        1900.0,
        2000.0,
        2100.0,
        2200.0,
        2300.0,
        2400.0,
        2500.0,
        2600.0,
        2700.0,
        2800.0,
        2900.0,
        3000.0,
        3100.0,
        3200.0,
        3300.0,
        3400.0,
        3500.0,
        3600.0,
        3700.0,
        3800.0,
        3900.0,
        4000.0,
        4100.0,
        4200.0,
        4300.0,
        4400.0,
        4500.0,
        4600.0,
        4700.0,
        4800.0,
        4900.0,
        5000.0,
        5100.0,
        5200.0,
        5300.0,
        5400.0,
        5500.0,
        5600.0,
        5700.0,
        5800.0,
        5900.0,
        6000.0,
    ],
}
