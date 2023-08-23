from __future__ import annotations

from emmet.core.molecules.redox import RedoxDoc
from emmet.core.mpid import MPculeID

from mp_api.client.core import BaseRester


class MoleculesRedoxRester(BaseRester[RedoxDoc]):
    suffix = "molecules/redox"
    document_model = RedoxDoc
    primary_key = "property_id"

    def search(
        self,
        molecule_ids: MPculeID | list[MPculeID] | None = None,
        property_ids: str | list[str] | None = None,
        charge: int | None = None,
        spin_multiplicity: int | None = None,
        level_of_theory: str | None = None,
        solvent: str | None = None,
        lot_solvent: str | None = None,
        formula: str | list[str] | None = None,
        elements: list[str] | None = None,
        exclude_elements: list[str] | None = None,
        chemsys: str | list[str] | None = None,
        electrode: str | None = None,
        min_reduction_potential: float | None = None,
        max_reduction_potential: float | None = None,
        min_oxidation_potential: float | None = None,
        max_oxidation_potential: float | None = None,
        electron_affinity: tuple[float, float] | None = None,
        ionization_energy: tuple[float, float] | None = None,
        reduction_energy: tuple[float, float] | None = None,
        reduction_free_energy: tuple[float, float] | None = None,
        oxidation_energy: tuple[float, float] | None = None,
        oxidation_free_energy: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        sort_fields: list[str] | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query molecules redox docs using a variety of search criteria.

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
            formula (str, List[str]): An alphabetical formula or list of formulas
                (e.g. "C2 Li2 O4", ["C2 H4", "C2 H6"]).
            elements (List[str]): A list of elements.
            exclude_elements (List(str)): List of elements to exclude.
            chemsys (str, List[str]): A chemical system, list of chemical systems
                (e.g., Li-C-O, [C-O-H-N, Li-N]), or single formula (e.g., C2 H4).
            electrode (str): For redox potential queries, a string representation of the reference
                electrode (currently accepted: "H", "Li", "Mg", "Ca")
            min_reduction_potential (float): Minimum reduction potential considered
            max_reduction_potential (float): Maximum reduction potential considered
            min_oxidation_potential (float): Minimum oxidation potential considered
            max_oxidation_potential (float): Maximum oxidation potential considered
            electron_affinity (Tuple[float, float]): Minimum and maximum electron affinities
            ionization_energy (Tuple[float, float]): Minimum and maximum ionization energies
            reduction_energy (Tuple[float, float]): Minimum and maximum reduction energies
            reduction_free_energy (Tuple[float, float]): Minimum and maximum reduction free energies
            oxidation_energy (Tuple[float, float]): Minimum and maximum oxidation energies
            oxidation_free_energy (Tuple[float, float]): Minimum and maximum oxidation free energies
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
            "electron_affinity",
            "ionization_energy",
            "reduction_energy",
            "reduction_free_energy",
            "oxidation_energy",
            "oxidation_free_energy",
        ]

        for param, value in locals().items():
            if param in min_max and value:
                if isinstance(value, (int, float)):
                    value = (value, value)
                query_params.update(
                    {
                        f"{param}_min": value[0],
                        f"{param}_max": value[1],
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

        if electrode:
            query_params.update({"electrode": electrode})

        if min_reduction_potential:
            query_params.update({"min_reduction_potential": min_reduction_potential})

        if max_reduction_potential:
            query_params.update({"max_reduction_potential": max_reduction_potential})

        if min_oxidation_potential:
            query_params.update({"min_oxidation_potential": min_oxidation_potential})

        if max_oxidation_potential:
            query_params.update({"max_oxidation_potential": max_oxidation_potential})

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
