"""Compute the oxygen evolution of a phase."""
from __future__ import annotations

import json
from collections.abc import Sequence
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.core import Composition, Element
from scipy.constants import Avogadro, Boltzmann, atm, elementary_charge
from scipy.interpolate import make_splrep, splev

DEFAULT_CACHE_FILE = Path(__file__).absolute().parent / "JANAF_O2_data.json"


class OxygenEvolution:
    """Compute the oxygen evolution using experimental data and atomistic phase diagrams.

    Parameters
    -----------
    """

    def __init__(
        self,
        cache_file: Path | None = DEFAULT_CACHE_FILE,
    ):
        self._spline_pars = None
        self.cache_file = cache_file

    def get_chempot_temp_data(
        self,
        nist_url: str = "https://janaf.nist.gov/tables/O-029.txt",
        ref_p: float = 0.21
        * atm
        * 1e-6,  # O2 partial pressure at ambient conditions, in MPa
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
        mu_o2_ref : float | None = None
            If a float, the O2 chemical potential at 0K.
            If None, this is determined from MP's data.

        Returns:
        -----------
        tuple of
            Temperature in K (np.ndarray)
            O2 chemical potential in eV/atom (np.ndarray)
        """
        if self.cache_file and self.cache_file.exists():
            data = json.loads(self.cache_file.read_text())
            return tuple(np.array(data[k]) for k in ("temperature", "mu-mu_0K"))

        response = requests.get(nist_url)

        with StringIO(initial_value=response.content.decode()) as stio:
            janaf_data = pd.read_csv(stio, sep="\t", header=1)

        kB_eV = Boltzmann / elementary_charge

        temp_K = janaf_data["T(K)"].to_numpy()
        entropy_dimless = janaf_data["S"].to_numpy() / (Boltzmann * Avogadro)

        mu_mu0 = kB_eV * temp_K * (1.0 + np.log(meas_p / ref_p) - entropy_dimless)
        if self.cache_file:
            self.cache_file.write_text(
                json.dumps(
                    {"mu-mu_0K": mu_mu0.tolist(), "temperature": temp_K.tolist()},
                )
            )

        return temp_K, mu_mu0

    @property
    def mu_to_temp_spline_params(self):
        if self._spline_pars is None:
            temp, mu_m0 = self.get_chempot_temp_data()

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
        return splev(np.array(mu), self.mu_to_temp_spline_params)

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
        new_z[1::2] = z[isort][1:]

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

        target_comp = Composition({"O": 1})
        for formula, data in by_dict.items():
            for idx, entry in enumerate(data):
                # Normalize all reactions to have integer coefficients
                scale = entry["reaction"].normalized_repr_and_factor()[1]
                by_dict[formula][idx]["reaction"]._coeffs = [
                    c * scale for c in entry["reaction"]._coeffs
                ]

                by_dict[formula][idx]["O2_produced"] = (
                    entry["reaction"].get_coeff(target_comp)
                    if target_comp in entry["reaction"].products
                    else 0
                )

        oxy_evo_data = {
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
            oxy_evo_data[formula][
                "evolution"
            ] *= -0.5  # This is the normalization convention we adopt for MP
            oxy_evo_data[formula]["temperature"] = self.mu_to_temp_spline(
                data["mu"] - mu_0K
            )
        return oxy_evo_data
