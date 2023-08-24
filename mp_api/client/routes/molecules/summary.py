from __future__ import annotations

from collections import defaultdict

from emmet.core.molecules.summary import HasProps, MoleculeSummaryDoc
from emmet.core.mpid import MPculeID

from mp_api.client.core import BaseRester


class MoleculesSummaryRester(BaseRester[MoleculeSummaryDoc]):
    suffix = "molecules/summary"
    document_model = MoleculeSummaryDoc  # type: ignore
    primary_key = "molecule_id"

    def search(
        self,
        charge: int | None = None,
        spin_multiplicity: int | None = None,
        nelements: tuple[int, int] | None = None,
        chemsys: str | list[str] | None = None,
        deprecated: bool | None = None,
        elements: list[str] | None = None,
        exclude_elements: list[str] | None = None,
        formula: str | list[str] | None = None,
        has_props: list[HasProps] | None = None,
        molecule_ids: list[MPculeID] | None = None,
        # has_solvent: Optional[Union[str, List[str]]] = None,
        # has_level_of_theory: Optional[Union[str, List[str]]] = None,
        # has_lot_solvent: Optional[Union[str, List[str]]] = None,
        # with_solvent: Optional[str] = None,
        # num_sites: Optional[Tuple[int, int]] = None,
        sort_fields: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query core data using a variety of search criteria.

        Arguments:
            charge (int): Minimum and maximum charge for the molecule.
            spin_multiplicity (int): Minimum and maximum spin for the molecule.
            nelements (Tuple[int, int]): Minimum and maximum number of elements
            # has_solvent (str, List[str]): Whether the molecule has properties calculated in
            #     solvents (e.g., "SOLVENT=THF", ["SOLVENT=WATER", "VACUUM"])
            # has_level_of_theory (str, List[str]): Whether the molecule has properties calculated
            #     using a particular level of theory (e.g. "wB97M-V/def2-SVPD/SMD",
            #         ["wB97X-V/def2-TZVPPD/SMD", "wB97M-V/def2-QZVPPD/SMD"])
            # has_lot_solvent (str, List[str]): Whether the molecule has properties calculated
            #     using a particular combination of level of theory and solvent (e.g.
            #         "wB97X-V/def2-SVPD/SMD(SOLVENT=THF)",
            #         ["wB97X-V/def2-TZVPPD/SMD(VACUUM)", "wB97M-V/def2-QZVPPD/SMD(SOLVENT=WATER)"])
            chemsys (str, List[str]): A chemical system, list of chemical systems
                (e.g., Li-C-O, [C-O-H-N, Li-N]), or single formula (e.g., C2 H4).
            deprecated (bool): Whether the material is tagged as deprecated.
            elements (List[str]): A list of elements.
            exclude_elements (List(str)): List of elements to exclude.
            formula (str, List[str]): An alphabetical formula or list of formulas
                (e.g. "C2 Li2 O4", ["C2 H4", "C2 H6"]).
            has_props: (List[HasProps]): The calculated properties available for the material.
            molecule_ids (List[MPculeID]): List of Materials Project Molecule IDs (MPculeIDs) to return data for.
            sort_fields (List[str]): Fields used to sort results. Prefixing with '-' will sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in SearchDoc to return data for.
                Default is material_id if all_fields is False.

        Returns:
            ([MoleculeSummaryDoc]) List of molecules summary documents
        """
        query_params = defaultdict(dict)  # type: dict

        min_max = [
            "nelements",
            "ionization_energy",
            "electron_affinity",
            "reduction_free_energy",
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
            query_params.update({"molecule_ids": ",".join(molecule_ids)})

        if charge:
            query_params.update({"charge": charge})

        if spin_multiplicity:
            query_params.update({"spin_multiplicity": spin_multiplicity})

        if deprecated is not None:
            query_params.update({"deprecated": deprecated})

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

        if exclude_elements is not None:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if has_props:
            query_params.update({"has_props": ",".join([i.value for i in has_props])})

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
