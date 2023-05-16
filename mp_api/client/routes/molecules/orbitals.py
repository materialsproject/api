from typing import List, Optional, Tuple, Union

from emmet.core.molecules.orbitals import OrbitalDoc
from emmet.core.mpid import MPculeID

from mp_api.client.core import BaseRester


class MoleculesOrbitalsRester(BaseRester[OrbitalDoc]):
    suffix = "molecules/orbitals"
    document_model = OrbitalDoc
    primary_key = "property_id"

    def search(
        self,
        molecule_ids: Optional[Union[MPculeID, List[MPculeID]]] = None,
        property_ids: Optional[Union[str, List[str]]] = None,
        charge: Optional[int] = None,
        spin_multiplicity: Optional[int] = None,
        level_of_theory: Optional[str] = None,
        solvent: Optional[str] = None,
        lot_solvent: Optional[str] = None,
        formula: Optional[Union[str, List[str]]] = None,
        elements: Optional[List[str]] = None,
        exclude_elements: Optional[List[str]] = None,
        chemsys: Optional[Union[str, List[str]]] = None,
        electron_type_population: Optional[str] = None,
        core_electrons: Optional[Tuple[float, float]] = None,
        valence_electrons: Optional[Tuple[float, float]] = None,
        rydberg_electrons: Optional[Tuple[float, float]] = None,
        total_electrons: Optional[Tuple[float, float]] = None,
        electron_type_lp: Optional[str] = None,
        lp_type: Optional[str] = None,
        s_character: Optional[Tuple[float, float]] = None,
        p_character: Optional[Tuple[float, float]] = None,
        d_character: Optional[Tuple[float, float]] = None,
        f_character: Optional[Tuple[float, float]] = None,
        lp_occupancy: Optional[Tuple[float, float]] = None,
        electron_type_bond: Optional[str] = None,
        bond_type: Optional[str] = None,
        s_character_atom1: Optional[Tuple[float, float]] = None,
        s_character_atom2: Optional[Tuple[float, float]] = None,
        p_character_atom1: Optional[Tuple[float, float]] = None,
        p_character_atom2: Optional[Tuple[float, float]] = None,
        d_character_atom1: Optional[Tuple[float, float]] = None,
        d_character_atom2: Optional[Tuple[float, float]] = None,
        f_character_atom1: Optional[Tuple[float, float]] = None,
        f_character_atom2: Optional[Tuple[float, float]] = None,
        polarization_atom1: Optional[Tuple[float, float]] = None,
        polarization_atom2: Optional[Tuple[float, float]] = None,
        bond_occupancy: Optional[Tuple[float, float]] = None,
        electron_type_interaction: Optional[str] = None,
        donor_type: Optional[str] = None,
        acceptor_type: Optional[str] = None,
        perturbation_energy: Optional[Tuple[float, float]] = None,
        energy_difference: Optional[Tuple[float, float]] = None,
        fock_element: Optional[Tuple[float, float]] = None,
        num_chunks: Optional[int] = None,
        sort_fields: Optional[List[str]] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query molecules redox docs using a variety of search criteria.

        Arguments:
            molecule_ids (MPculeID, List[MPculeID]): List of Materials Project Molecule IDs (MPculeIDs) to return data
                for.
            property_ids (str, List[str]): List of property IDs to return data for.
            charge (Tuple[int, int]): Minimum and maximum charge for the molecule.
            spin_multiplicity (Tuple[int, int]): Minimum and maximum spin for the molecule.
            level_of_theory (str): Desired level of theory (e.g. "wB97X-V/def2-TZVPPD/SMD")
            solvent (str): Desired solvent (e.g. "SOLVENT=WATER")
            lot_solvent (str): Desired combination of level of theory and solvent
                (e.g. "wB97X-V/def2-TZVPPD/SMD(SOLVENT=THF)")
            correction_level_of_theory (str): Desired correction level of theory (e.g. "wB97X-V/def2-TZVPPD/SMD")
            correction_solvent (str): Desired correction solvent (e.g. "SOLVENT=WATER")
            correction_lot_solvent (str): Desired correction combination of level of theory and solvent
                (e.g. "wB97X-V/def2-TZVPPD/SMD(SOLVENT=THF)")
            combined_lot_solvent (str): Desired combination of level of theory and solvent including both main
                thermo calculation and single-point energy correction
                (e.g. "wB97X-D/def2-SVPD/VACUUM//wB97X-V/def2-TZVPPD/SMD(SOLVENT=THF)")
            formula (str, List[str]): An alphabetical formula or list of formulas
                (e.g. "C2 Li2 O4", ["C2 H4", "C2 H6"]).
            elements (List[str]): A list of elements.
            exclude_elements (List(str)): List of elements to exclude.
            chemsys (str, List[str]): A chemical system, list of chemical systems
                (e.g., Li-C-O, [C-O-H-N, Li-N]), or single formula (e.g., C2 H4).
            electron_type_population (str): Should alpha ('alpha'), beta ('beta'), or all electrons (None) be
                considered in a query of natural electron populations?
            core_electrons (Tuple[float, float]): Minimum and maximum number of core electrons in an atom
                in this molecule.
            valence_electrons (Tuple[float, float]): Minimum and maximum number of valence electrons in an atom
                in this molecule.
            rydberg_electrons (Tuple[float, float]): Minimum and maximum number of rydberg electrons in an atom
                in this molecule.
            total_electrons: (Tuple[float, float]): Minimum and maximum number of total electrons in an atom
                in this molecule.
            electron_type_lp (str): Should alpha ('alpha'), beta ('beta'), or all electrons (None) be
                considered in a query of lone pairs?
            lp_type (str): Type of orbital - "LP" for "lone pair" or "LV" for "lone vacant"
            s_character (Tuple[float, float]): Min and max percentage of the lone pair constituted by s atomic orbitals.
            p_character (Tuple[float, float]): Min and max percentage of the lone pair constituted by p atomic orbitals.
            d_character (Tuple[float, float]): Min and max percentage of the lone pair constituted by d atomic orbitals.
            f_character (Tuple[float, float]): Min and max percentage of the lone pair constituted by f atomic orbitals.
            lp_occupancy(Tuple[float, float]): Min and max number of electrons in the lone pair.
            electron_type_bond (str): Should alpha ('alpha'), beta ('beta'), or all electrons (None) be
                considered in a query of bonds?
            bond_type (str): Type of orbital, e.g. "BD" for bonding or "BD*" for antibonding
            s_character_atom1 (Tuple[float, float]): Min and max percentage of the bond constituted by s atomic orbitals
                on the first atom.
            s_character_atom2 (Tuple[float, float]): Min and max percentage of the bond constituted by s atomic orbitals
                on the second atom.
            p_character_atom1 (Tuple[float, float]): Min and max percentage of the bond constituted by p atomic orbitals
                on the first atom.
            p_character_atom2 (Tuple[float, float]): Min and max percentage of the bond constituted by p atomic orbitals
                on the second atom.
            d_character_atom1 (Tuple[float, float]): Min and max percentage of the bond constituted by d atomic orbitals
                on the first atom.
            d_character_atom2 (Tuple[float, float]): Min and max percentage of the bond constituted by d atomic orbitals
                on the second atom.
            f_character_atom1 (Tuple[float, float]): Min and max percentage of the bond constituted by f atomic orbitals
                on the first atom.
            f_character_atom2 (Tuple[float, float]): Min and max percentage of the bond constituted by f atomic orbitals
                on the second atom.
            polarization_atom1 (Tuple[float, float]): Min and max fraction of electrons in the bond donated by the
                first atom.
            polarization_atom2 (Tuple[float, float]): Min and max fraction of electrons in the bond donated by the
                second atom.
            bond_occupancy (Tuple[float, float]): Min and max number of electrons in the bond.
            electron_type_interaction (str): Should alpha ('alpha'), beta ('beta'), or all electrons (None) be
                considered in a query of orbital interactions?
            donor_type (str): Type of donor orbital, e.g. 'BD' for bonding or 'RY*' for anti-Rydberg
            acceptor_type (str): Type of acceptor orbital, e.g. 'BD' for bonding or 'RY*' for anti-Rydberg
            perturbation_energy (Tuple[float, float]): Min and max perturbation energy of the interaction
            energy_difference (Tuple[float, float]): Min and max energy difference between interacting orbitals
            fock_element (Tuple[float, float]): Min and max interaction Fock matrix element
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MoleculeDoc to return data for.
                Default is "molecule_id", "property_id", "solvent", "method", "last_updated"
                if all_fields is False.

        Returns:
            ([RedoxDoc]) List of molecule redox documents
        """

        query_params = {}  # type: dict

        min_max = [
            "core_electrons",
            "valence_electrons",
            "rydberg_electrons",
            "total_electrons",
            "s_character",
            "p_character",
            "d_character",
            "f_character",
            "lp_occupancy",
            "s_character_atom1",
            "s_character_atom2",
            "p_character_atom1",
            "p_character_atom2",
            "d_character_atom1",
            "d_character_atom2",
            "f_character_atom1",
            "f_character_atom2",
            "polarization_atom1",
            "polarization_atom2",
            "bond_occupancy",
            "perturbation_energy",
            "energy_difference",
            "fock_element",
        ]

        for param, value in locals().items():
            if param in min_max and value:
                if isinstance(value, (int, float)):
                    value = (value, value)
                query_params.update(
                    {
                        f"min_{param}": value[0],
                        f"max_{param}": value[1],
                    }
                )

        if molecule_ids:
            if isinstance(molecule_ids, str):
                molecule_ids = [molecule_ids]

            query_params.update({"molecule_ids": ",".join(molecule_ids)})

        if property_ids:
            if isinstance(property_ids, str):
                property_ids = [property_ids]

            query_params.update({"property_ids": ",".join(property_ids)})

        if charge:
            query_params.update({"charge": charge})

        if spin_multiplicity:
            query_params.update({"spin_multiplicity": spin_multiplicity})

        if level_of_theory:
            query_params.update({"level_of_theory": level_of_theory})

        if solvent:
            query_params.update({"solvent": solvent})

        if lot_solvent:
            query_params.update({"lot_solvent": lot_solvent})

        if formula:
            if isinstance(formula, str):
                formula = [formula]

            query_params.update({"formula": ",".join(formula)})

        if chemsys:
            if isinstance(chemsys, str):
                chemsys = [chemsys]

            query_params.update({"chemsys": ",".join(chemsys)})

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if exclude_elements:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if electron_type_population:
            query_params.update({"electron_type_population": electron_type_population})

        if electron_type_lp:
            query_params.update({"electron_type_lp": electron_type_lp})

        if lp_type:
            query_params.update({"lp_type": lp_type})

        if electron_type_bond:
            query_params.update({"electron_type_bond": electron_type_bond})

        if bond_type:
            query_params.update({"bond_type": bond_type})

        if electron_type_interaction:
            query_params.update(
                {"electron_type_interaction": electron_type_interaction}
            )

        if donor_type:
            query_params.update({"donor_type": donor_type})

        if acceptor_type:
            query_params.update({"acceptor_type": acceptor_type})

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
