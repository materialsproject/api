# ruff: noqa
from __future__ import annotations

from datetime import datetime
from typing import Literal, Any

import plotly.graph_objects as plotly_go

from emmet.core.chemenv import (
    COORDINATION_GEOMETRIES,
    COORDINATION_GEOMETRIES_IUCR,
    COORDINATION_GEOMETRIES_IUPAC,
    COORDINATION_GEOMETRIES_NAMES,
)
from emmet.core.electronic_structure import BSPathType, DOSProjectionType
from emmet.core.grain_boundary import GBTypeEnum
from emmet.core.mpid import MPID
from emmet.core.summary import HasProps
from emmet.core.symmetry import CrystalSystem
from emmet.core.synthesis import OperationTypeEnum, SynthesisTypeEnum
from emmet.core.thermo import ThermoType
from emmet.core.vasp.calc_types import CalcType
from emmet.core.xas import Edge, Type
from pymatgen.analysis.magnetism.analyzer import Ordering
from pymatgen.core.periodic_table import Element
from pymatgen.core.composition import Composition
from pymatgen.core.structure import Structure
from pymatgen.electronic_structure.core import OrbitalType, Spin
from pymatgen.entries.computed_entries import ComputedEntry

from mp_api.mcp.utils import _NeedsMPClient


class MPMcpTools(_NeedsMPClient):
    """Define tools needed for the MP MCP client."""

    def get_structure_by_material_id(
        self,
        material_id: str,
        structure_format: Literal["json", "poscar", "cif"],
    ) -> dict[str, Any] | str:
        """Find a structure in the Materials Project by its identifier/ID.

        Return type changes based on format:
            structure_format = "json":
                Returns the JSON representation of a pymatgen structure object.
            structure_format = "poscar":
                Returns a VASP POSCAR-like representation
            structure_format = "cif":
                Returns a crystallographic information file (CIF)
        """
        struct = self.client.get_structure_by_material_id(
            material_id=material_id,
            final=True,
            conventional_unit_cell=False,
        )
        if structure_format == "json":
            return struct.as_dict() if hasattr(struct, "as_dict") else struct

        if isinstance(struct, dict):
            struct = Structure.from_dict(struct)
        return struct.to(fmt=structure_format)

    def get_phase_diagram_from_elements(
        self,
        elements: list[str],
        thermo_type: ThermoType | str = "GGA_GGA+U_R2SCAN",
    ) -> plotly_go.Figure:
        """Find a thermodynamic phase diagram in the Materials Project by specified elements.

        ### Examples:
        Given elements Na and Cl:
        ```
        phase_diagram = MPMcpTools().get_phase_diagram_from_elements(
            elements = ["Na","Cl"],
        )
        ```

        Given a chemical system, "K-P-O":
        ```
        phase_diagrasm =  MPMcpTools().get_phase_diagram_from_elements(
            elements = "K-P-O".split("-"),
        )
        ```

        """
        pd = self.client.materials.thermo.get_phase_diagram_from_chemsys(
            "-".join(elements), thermo_type
        )
        return pd.get_plot()  # has to be JSON serializable

    def get_stability_or_energy_above_hull(
        self,
        formula: str,
        energy: float,
        run_type: Literal["GGA", "PBE", "GGA+U", "PBE+U", "R2SCAN"],
    ) -> float:
        """Get the stability of a particular material.

        Given a material's formula and energy in eV, tells you the material's
        stability from the energy above the hull (positive for unstable, 0 for stable)
        in eV/atom.

        The user must specify a particular functional:
            - PBE or GGA
            - PBE+U or GGA+U
            - R2SCAN
        this will add necessary corrections to the energy to compare with
        the Materials Project.

        """
        run_type = run_type.replace("PBE", "GGA")
        data = {"run_type": run_type}
        thermo_type = "GGA_GGA+U" if run_type in {"GGA", "GGA+U"} else "R2SCAN"

        try:
            stability = self.client.get_stability(
                entries=[ComputedEntry(Composition(formula), energy, data=data)],
                thermo_type=thermo_type,
            )
            return stability[0]["e_above_hull"]
        except ValueError:
            return float("inf")

    def get_absorption_data(
        self,
        material_ids: str | list[str] | None = None,
        chemsys: str | list[str] | None = None,
        elements: list[str] | None = None,
        exclude_elements: list[str] | None = None,
        formula: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.absorption.search(
            material_ids=material_ids,
            chemsys=chemsys,
            elements=elements,
            exclude_elements=exclude_elements,
            formula=formula,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_bonds_data(
        self,
        material_ids: str | list[str] | None = None,
        coordination_envs: list[str] | None = None,
        coordination_envs_anonymous: list[str] | None = None,
        max_bond_length: tuple[float, float] | None = None,
        mean_bond_length: tuple[float, float] | None = None,
        min_bond_length: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.bonds.search(
            material_ids=material_ids,
            coordination_envs=coordination_envs,
            coordination_envs_anonymous=coordination_envs_anonymous,
            max_bond_length=max_bond_length,
            mean_bond_length=mean_bond_length,
            min_bond_length=min_bond_length,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_chemical_environment_data(
        self,
        material_ids: str | list[str] | None = None,
        chemenv_iucr: COORDINATION_GEOMETRIES_IUCR
        | list[COORDINATION_GEOMETRIES_IUCR]
        | None = None,
        chemenv_iupac: COORDINATION_GEOMETRIES_IUPAC
        | list[COORDINATION_GEOMETRIES_IUPAC]
        | None = None,
        chemenv_name: COORDINATION_GEOMETRIES_NAMES
        | list[COORDINATION_GEOMETRIES_NAMES]
        | None = None,
        chemenv_symbol: COORDINATION_GEOMETRIES
        | list[COORDINATION_GEOMETRIES]
        | None = None,
        species: str | list[str] | None = None,
        elements: str | list[str] | None = None,
        exclude_elements: list[str] | None = None,
        csm: tuple[float, float] | None = None,
        density: tuple[float, float] | None = None,
        num_elements: tuple[int, int] | None = None,
        num_sites: tuple[int, int] | None = None,
        volume: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.chemenv.search(
            material_ids=material_ids,
            chemenv_iucr=chemenv_iucr,
            chemenv_iupac=chemenv_iupac,
            chemenv_name=chemenv_name,
            chemenv_symbol=chemenv_symbol,
            species=species,
            elements=elements,
            exclude_elements=exclude_elements,
            csm=csm,
            density=density,
            num_elements=num_elements,
            num_sites=num_sites,
            volume=volume,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_dielectric_data(
        self,
        material_ids: str | list[str] | None = None,
        e_total: tuple[float, float] | None = None,
        e_ionic: tuple[float, float] | None = None,
        e_electronic: tuple[float, float] | None = None,
        n: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.dielectric.search(
            material_ids=material_ids,
            e_total=e_total,
            e_ionic=e_ionic,
            e_electronic=e_electronic,
            n=n,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_elasticity_data(
        self,
        material_ids: str | list[str] | None = None,
        elastic_anisotropy: tuple[float, float] | None = None,
        g_voigt: tuple[float, float] | None = None,
        g_reuss: tuple[float, float] | None = None,
        g_vrh: tuple[float, float] | None = None,
        k_voigt: tuple[float, float] | None = None,
        k_reuss: tuple[float, float] | None = None,
        k_vrh: tuple[float, float] | None = None,
        poisson_ratio: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.elasticity.search(
            material_ids=material_ids,
            elastic_anisotropy=elastic_anisotropy,
            g_voigt=g_voigt,
            g_reuss=g_reuss,
            g_vrh=g_vrh,
            k_voigt=k_voigt,
            k_reuss=k_reuss,
            k_vrh=k_vrh,
            poisson_ratio=poisson_ratio,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_insertion_electrodes_data(
        self,
        material_ids: str | list[str] | None = None,
        battery_ids: str | list[str] | None = None,
        average_voltage: tuple[float, float] | None = None,
        capacity_grav: tuple[float, float] | None = None,
        capacity_vol: tuple[float, float] | None = None,
        elements: list[str] | None = None,
        energy_grav: tuple[float, float] | None = None,
        energy_vol: tuple[float, float] | None = None,
        exclude_elements: list[str] | None = None,
        formula: str | list[str] | None = None,
        fracA_charge: tuple[float, float] | None = None,
        fracA_discharge: tuple[float, float] | None = None,
        max_delta_volume: tuple[float, float] | None = None,
        max_voltage_step: tuple[float, float] | None = None,
        num_elements: tuple[int, int] | None = None,
        num_steps: tuple[int, int] | None = None,
        stability_charge: tuple[float, float] | None = None,
        stability_discharge: tuple[float, float] | None = None,
        working_ion: Element | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.insertion_electrodes.search(
            material_ids=material_ids,
            battery_ids=battery_ids,
            average_voltage=average_voltage,
            capacity_grav=capacity_grav,
            capacity_vol=capacity_vol,
            elements=elements,
            energy_grav=energy_grav,
            energy_vol=energy_vol,
            exclude_elements=exclude_elements,
            formula=formula,
            fracA_charge=fracA_charge,
            fracA_discharge=fracA_discharge,
            max_delta_volume=max_delta_volume,
            max_voltage_step=max_voltage_step,
            num_elements=num_elements,
            num_steps=num_steps,
            stability_charge=stability_charge,
            stability_discharge=stability_discharge,
            working_ion=working_ion,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_electronic_structure_data(
        self,
        material_ids: str | list[str] | None = None,
        band_gap: tuple[float, float] | None = None,
        chemsys: str | list[str] | None = None,
        efermi: tuple[float, float] | None = None,
        elements: list[str] | None = None,
        exclude_elements: list[str] | None = None,
        formula: str | list[str] | None = None,
        is_gap_direct: bool | None = None,
        is_metal: bool | None = None,
        magnetic_ordering: Ordering | None = None,
        num_elements: tuple[int, int] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.electronic_structure.search(
            material_ids=material_ids,
            band_gap=band_gap,
            chemsys=chemsys,
            efermi=efermi,
            elements=elements,
            exclude_elements=exclude_elements,
            formula=formula,
            is_gap_direct=is_gap_direct,
            is_metal=is_metal,
            magnetic_ordering=magnetic_ordering,
            num_elements=num_elements,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_electronic_structure_bandstructure_data(
        self,
        band_gap: tuple[float, float] | None = None,
        efermi: tuple[float, float] | None = None,
        is_gap_direct: bool | None = None,
        is_metal: bool | None = None,
        magnetic_ordering: Ordering | None = None,
        path_type: BSPathType = BSPathType.setyawan_curtarolo,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.electronic_structure_bandstructure.search(
            band_gap=band_gap,
            efermi=efermi,
            is_gap_direct=is_gap_direct,
            is_metal=is_metal,
            magnetic_ordering=magnetic_ordering,
            path_type=path_type,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_electronic_structure_density_of_states_data(
        self,
        band_gap: tuple[float, float] | None = None,
        efermi: tuple[float, float] | None = None,
        element: Element | None = None,
        magnetic_ordering: Ordering | None = None,
        orbital: OrbitalType | None = None,
        projection_type: DOSProjectionType = DOSProjectionType.total,
        spin: Spin = 1,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.electronic_structure_dos.search(
            band_gap=band_gap,
            efermi=efermi,
            element=element,
            magnetic_ordering=magnetic_ordering,
            orbital=orbital,
            projection_type=projection_type,
            spin=spin,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_equation_of_state_data(
        self,
        material_ids: str | list[str] | None = None,
        energies: tuple[float, float] | None = None,
        volumes: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.eos.search(
            material_ids=material_ids,
            energies=energies,
            volumes=volumes,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_grain_boundaries_data(
        self,
        material_ids: str | list[str] | None = None,
        chemsys: str | None = None,
        gb_plane: list[str] | None = None,
        gb_energy: tuple[float, float] | None = None,
        pretty_formula: str | None = None,
        rotation_axis: tuple[int, int, int] | tuple[int, int, int, int] | None = None,
        rotation_angle: tuple[float, float] | None = None,
        separation_energy: tuple[float, float] | None = None,
        sigma: int | None = None,
        type: GBTypeEnum | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.grain_boundaries.search(
            material_ids=material_ids,
            chemsys=chemsys,
            gb_plane=gb_plane,
            gb_energy=gb_energy,
            pretty_formula=pretty_formula,
            rotation_axis=rotation_axis,
            rotation_angle=rotation_angle,
            separation_energy=separation_energy,
            sigma=sigma,
            type=type,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_magnetism_data(
        self,
        material_ids: str | list[str] | None = None,
        num_magnetic_sites: tuple[int, int] | None = None,
        num_unique_magnetic_sites: tuple[int, int] | None = None,
        ordering: Ordering | None = None,
        total_magnetization: tuple[float, float] | None = None,
        total_magnetization_normalized_vol: tuple[float, float] | None = None,
        total_magnetization_normalized_formula_units: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.magnetism.search(
            material_ids=material_ids,
            num_magnetic_sites=num_magnetic_sites,
            num_unique_magnetic_sites=num_unique_magnetic_sites,
            ordering=ordering,
            total_magnetization=total_magnetization,
            total_magnetization_normalized_vol=total_magnetization_normalized_vol,
            total_magnetization_normalized_formula_units=total_magnetization_normalized_formula_units,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_oxidation_states_data(
        self,
        material_ids: str | list[str] | None = None,
        chemsys: str | list[str] | None = None,
        formula: str | list[str] | None = None,
        possible_species: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.oxidation_states.search(
            material_ids=material_ids,
            chemsys=chemsys,
            formula=formula,
            possible_species=possible_species,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_phonon_data(
        self,
        material_ids: str | list[str] | None = None,
        phonon_method: str | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.phonon.search(
            material_ids=material_ids,
            phonon_method=phonon_method,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_piezoelectric_data(
        self,
        material_ids: str | list[str] | None = None,
        piezoelectric_modulus: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.piezoelectric.search(
            material_ids=material_ids,
            piezoelectric_modulus=piezoelectric_modulus,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_provenance_data(
        self,
        material_ids: str | list[str] | None = None,
        deprecated: bool | None = False,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.provenance.search(
            material_ids=material_ids,
            deprecated=deprecated,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_crystal_summary_data(
        self,
        material_ids: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.robocrys.search(
            material_ids=material_ids,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_similarity_data(
        self,
        material_ids: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.similarity.search(
            material_ids=material_ids,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_substrates_data(
        self,
        area: tuple[float, float] | None = None,
        energy: tuple[float, float] | None = None,
        film_id: str | None = None,
        film_orientation: list[int] | None = None,
        substrate_id: str | None = None,
        substrate_formula: str | None = None,
        substrate_orientation: list[int] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.substrates.search(
            area=area,
            energy=energy,
            film_id=film_id,
            film_orientation=film_orientation,
            substrate_id=substrate_id,
            substrate_formula=substrate_formula,
            substrate_orientation=substrate_orientation,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_material_data(
        self,
        band_gap: tuple[float, float] | None = None,
        chemsys: str | list[str] | None = None,
        crystal_system: CrystalSystem | None = None,
        density: tuple[float, float] | None = None,
        deprecated: bool | None = None,
        e_electronic: tuple[float, float] | None = None,
        e_ionic: tuple[float, float] | None = None,
        e_total: tuple[float, float] | None = None,
        efermi: tuple[float, float] | None = None,
        elastic_anisotropy: tuple[float, float] | None = None,
        elements: list[str] | None = None,
        energy_above_hull: tuple[float, float] | None = None,
        equilibrium_reaction_energy: tuple[float, float] | None = None,
        exclude_elements: list[str] | None = None,
        formation_energy: tuple[float, float] | None = None,
        formula: str | list[str] | None = None,
        g_reuss: tuple[float, float] | None = None,
        g_voigt: tuple[float, float] | None = None,
        g_vrh: tuple[float, float] | None = None,
        has_props: list[HasProps] | list[str] | None = None,
        has_reconstructed: bool | None = None,
        is_gap_direct: bool | None = None,
        is_metal: bool | None = None,
        is_stable: bool | None = None,
        k_reuss: tuple[float, float] | None = None,
        k_voigt: tuple[float, float] | None = None,
        k_vrh: tuple[float, float] | None = None,
        magnetic_ordering: Ordering | None = None,
        material_ids: str | list[str] | None = None,
        n: tuple[float, float] | None = None,
        num_elements: tuple[int, int] | None = None,
        num_sites: tuple[int, int] | None = None,
        num_magnetic_sites: tuple[int, int] | None = None,
        num_unique_magnetic_sites: tuple[int, int] | None = None,
        piezoelectric_modulus: tuple[float, float] | None = None,
        poisson_ratio: tuple[float, float] | None = None,
        possible_species: list[str] | None = None,
        shape_factor: tuple[float, float] | None = None,
        spacegroup_number: int | None = None,
        spacegroup_symbol: str | None = None,
        surface_energy_anisotropy: tuple[float, float] | None = None,
        theoretical: bool | None = None,
        total_energy: tuple[float, float] | None = None,
        total_magnetization: tuple[float, float] | None = None,
        total_magnetization_normalized_formula_units: tuple[float, float] | None = None,
        total_magnetization_normalized_vol: tuple[float, float] | None = None,
        uncorrected_energy: tuple[float, float] | None = None,
        volume: tuple[float, float] | None = None,
        weighted_surface_energy: tuple[float, float] | None = None,
        weighted_work_function: tuple[float, float] | None = None,
        include_gnome: bool = True,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.summary.search(
            band_gap=band_gap,
            chemsys=chemsys,
            crystal_system=crystal_system,
            density=density,
            deprecated=deprecated,
            e_electronic=e_electronic,
            e_ionic=e_ionic,
            e_total=e_total,
            efermi=efermi,
            elastic_anisotropy=elastic_anisotropy,
            elements=elements,
            energy_above_hull=energy_above_hull,
            equilibrium_reaction_energy=equilibrium_reaction_energy,
            exclude_elements=exclude_elements,
            formation_energy=formation_energy,
            formula=formula,
            g_reuss=g_reuss,
            g_voigt=g_voigt,
            g_vrh=g_vrh,
            has_props=has_props,
            has_reconstructed=has_reconstructed,
            is_gap_direct=is_gap_direct,
            is_metal=is_metal,
            is_stable=is_stable,
            k_reuss=k_reuss,
            k_voigt=k_voigt,
            k_vrh=k_vrh,
            magnetic_ordering=magnetic_ordering,
            material_ids=material_ids,
            n=n,
            num_elements=num_elements,
            num_sites=num_sites,
            num_magnetic_sites=num_magnetic_sites,
            num_unique_magnetic_sites=num_unique_magnetic_sites,
            piezoelectric_modulus=piezoelectric_modulus,
            poisson_ratio=poisson_ratio,
            possible_species=possible_species,
            shape_factor=shape_factor,
            spacegroup_number=spacegroup_number,
            spacegroup_symbol=spacegroup_symbol,
            surface_energy_anisotropy=surface_energy_anisotropy,
            theoretical=theoretical,
            total_energy=total_energy,
            total_magnetization=total_magnetization,
            total_magnetization_normalized_formula_units=total_magnetization_normalized_formula_units,
            total_magnetization_normalized_vol=total_magnetization_normalized_vol,
            uncorrected_energy=uncorrected_energy,
            volume=volume,
            weighted_surface_energy=weighted_surface_energy,
            weighted_work_function=weighted_work_function,
            include_gnome=include_gnome,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_surface_properties_data(
        self,
        material_ids: str | list[str] | None = None,
        has_reconstructed: bool | None = None,
        shape_factor: tuple[float, float] | None = None,
        surface_energy_anisotropy: tuple[float, float] | None = None,
        weighted_surface_energy: tuple[float, float] | None = None,
        weighted_work_function: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.surface_properties.search(
            material_ids=material_ids,
            has_reconstructed=has_reconstructed,
            shape_factor=shape_factor,
            surface_energy_anisotropy=surface_energy_anisotropy,
            weighted_surface_energy=weighted_surface_energy,
            weighted_work_function=weighted_work_function,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_synthesis_data(
        self,
        keywords: list[str] | None = None,
        synthesis_type: list[SynthesisTypeEnum] | None = None,
        target_formula: str | None = None,
        precursor_formula: str | None = None,
        operations: list[OperationTypeEnum] | None = None,
        condition_heating_temperature_min: float | None = None,
        condition_heating_temperature_max: float | None = None,
        condition_heating_time_min: float | None = None,
        condition_heating_time_max: float | None = None,
        condition_heating_atmosphere: list[str] | None = None,
        condition_mixing_device: list[str] | None = None,
        condition_mixing_media: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int | None = 10,
    ) -> list[dict]:
        return self.client.materials.synthesis.search(
            keywords=keywords,
            synthesis_type=synthesis_type,
            target_formula=target_formula,
            precursor_formula=precursor_formula,
            operations=operations,
            condition_heating_temperature_min=condition_heating_temperature_min,
            condition_heating_temperature_max=condition_heating_temperature_max,
            condition_heating_time_min=condition_heating_time_min,
            condition_heating_time_max=condition_heating_time_max,
            condition_heating_atmosphere=condition_heating_atmosphere,
            condition_mixing_device=condition_mixing_device,
            condition_mixing_media=condition_mixing_media,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
        )

    def get_tasks_data(
        self,
        task_ids: str | list[str] | None = None,
        elements: list[str] | None = None,
        exclude_elements: list[str] | None = None,
        formula: str | list[str] | None = None,
        last_updated: tuple[datetime, datetime] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.tasks.search(
            task_ids=task_ids,
            elements=elements,
            exclude_elements=exclude_elements,
            formula=formula,
            last_updated=last_updated,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_thermo_data(
        self,
        material_ids: str | list[str] | None = None,
        chemsys: str | list[str] | None = None,
        energy_above_hull: tuple[float, float] | None = None,
        equilibrium_reaction_energy: tuple[float, float] | None = None,
        formation_energy: tuple[float, float] | None = None,
        formula: str | list[str] | None = None,
        is_stable: bool | None = None,
        num_elements: tuple[int, int] | None = None,
        thermo_ids: list[str] | None = None,
        thermo_types: list[ThermoType | str] | None = None,
        total_energy: tuple[float, float] | None = None,
        uncorrected_energy: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.thermo.search(
            material_ids=material_ids,
            chemsys=chemsys,
            energy_above_hull=energy_above_hull,
            equilibrium_reaction_energy=equilibrium_reaction_energy,
            formation_energy=formation_energy,
            formula=formula,
            is_stable=is_stable,
            num_elements=num_elements,
            thermo_ids=thermo_ids,
            thermo_types=thermo_types,
            total_energy=total_energy,
            uncorrected_energy=uncorrected_energy,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_xas_data(
        self,
        edge: Edge | None = None,
        absorbing_element: Element | None = None,
        formula: str | None = None,
        chemsys: str | list[str] | None = None,
        elements: list[str] | None = None,
        material_ids: list[str] | None = None,
        spectrum_type: Type | None = None,
        spectrum_ids: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.xas.search(
            edge=edge,
            absorbing_element=absorbing_element,
            formula=formula,
            chemsys=chemsys,
            elements=elements,
            material_ids=material_ids,
            spectrum_type=spectrum_type,
            spectrum_ids=spectrum_ids,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_alloys_data(
        self,
        material_ids: str | list[str] | None = None,
        formulae: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[dict]:
        return self.client.materials.alloys.search(
            material_ids=material_ids,
            formulae=formulae,
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
        )

    def get_structure(
        self,
        filename_or_structure: str | Structure,
        ltol: float = 0.2,
        stol: float = 0.3,
        angle_tol: float = 5.0,
        allow_multiple_results: bool = False,
    ) -> list[dict]:
        return self.client.find_structure(
            filename_or_structure=filename_or_structure,
            ltol=ltol,
            stol=stol,
            angle_tol=angle_tol,
            allow_multiple_results=allow_multiple_results,
        )

    def get_bandstructure_by_material_id(
        self,
        material_id: str = BSPathType.setyawan_curtarolo,
        path_type: BSPathType = True,
    ) -> list[dict]:
        return self.client.get_bandstructure_by_material_id(
            material_id=material_id, path_type=path_type
        )

    def get_charge_density_from_material_id(
        self, material_id: str, inc_task_doc: bool = False
    ) -> list[dict]:
        return self.client.get_charge_density_from_material_id(
            material_id=material_id, inc_task_doc=inc_task_doc
        )

    def get_charge_density_from_task_id(
        self, task_id: str, inc_task_doc: bool = False
    ) -> list[dict]:
        return self.client.get_charge_density_from_task_id(
            task_id=task_id, inc_task_doc=inc_task_doc
        )

    def get_cohesive_energy(
        self,
        material_ids: list[MPID | str],
        normalization: Literal["atom", "formula_unit"] = "atom",
    ) -> list[dict]:
        return self.client.get_cohesive_energy(
            material_ids=material_ids, normalization=normalization
        )

    def get_entries(
        self,
        chemsys_formula_mpids: str | list[str],
        compatible_only: bool = True,
        inc_structure: bool | None = None,
        property_data: list[str] | None = None,
        conventional_unit_cell: bool = False,
        additional_criteria: dict | None = None,
    ) -> list[dict]:
        return self.client.get_entries(
            chemsys_formula_mpids=chemsys_formula_mpids,
            compatible_only=compatible_only,
            inc_structure=inc_structure,
            property_data=property_data,
            conventional_unit_cell=conventional_unit_cell,
            additional_criteria=additional_criteria,
        )

    def get_entries_in_chemsys(
        self,
        elements: str | list[str],
        use_gibbs: int | None = None,
        compatible_only: bool = True,
        inc_structure: bool | None = None,
        property_data: list[str] | None = None,
        conventional_unit_cell: bool = False,
        additional_criteria: dict = None,
    ) -> list[dict]:
        if additional_criteria is None:
            additional_criteria = {"thermo_types": ["GGA_GGA+U"]}
        return self.client.get_entries_in_chemsys(
            elements=elements,
            use_gibbs=use_gibbs,
            compatible_only=compatible_only,
            inc_structure=inc_structure,
            property_data=property_data,
            conventional_unit_cell=conventional_unit_cell,
            additional_criteria=additional_criteria,
        )

    def get_entry_by_material_id(
        self,
        material_id: str,
        compatible_only: bool = True,
        inc_structure: bool | None = None,
        property_data: list[str] | None = None,
        conventional_unit_cell: bool = False,
    ) -> list[dict]:
        return self.client.get_entry_by_material_id(
            material_id=material_id,
            compatible_only=compatible_only,
            inc_structure=inc_structure,
            property_data=property_data,
            conventional_unit_cell=conventional_unit_cell,
        )

    def get_structures(self, chemsys_formula: str | list[str] = True) -> list[dict]:
        return self.client.get_structures(chemsys_formula=chemsys_formula)

    def get_task_ids_associated_with_material_id(
        self, material_id: str, calc_types: list[CalcType] | None = None
    ) -> list[dict]:
        return self.client.get_task_ids_associated_with_material_id(
            material_id=material_id, calc_types=calc_types
        )
