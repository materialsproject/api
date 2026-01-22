"""Define core molecules functionality.

Note that these classes are not currently working.
The `MoleculeRester` methods: `search`, `find_molecule`, `get_molecule_by_mpculeid`,
all return 404s when attempting to use them.
"""

from __future__ import annotations

from emmet.core.mpid import MPculeID
from emmet.core.qchem.molecule import MoleculeDoc
from pymatgen.core.structure import Molecule

from mp_api.client.core.client import CoreRester, MPRestError
from mp_api.client.core.utils import validate_ids
from mp_api.client.routes.molecules import MOLECULES_RESTERS


class BaseMoleculeRester(CoreRester):
    document_model = MoleculeDoc
    primary_key = "molecule_id"

    def get_molecule_by_mpculeid(
        self, mpcule_id: str, final: bool = True
    ) -> Molecule | list[Molecule]:
        """Get a molecule object for a given Materials Project molecules ID (MPculeID).

        Arguments:
            mpcule_id (str): Materials project molecule ID
            final (bool): Whether to get the final (optimized) molecule, or the list of initial
                (pre-optimized) structures. Defaults to True.

        Returns:
            molecule (Union[Molecule, List[Molecule]]): Pymatgen Molecule object or list of
                pymatgen Molecule objects.
        """
        field = "molecule" if final else "initial_molecules"

        response = self.search(molecule_ids=[mpcule_id], fields=[field])  # type: ignore
        return response[0][field] if (response and response[0]) else response  # type: ignore

    def find_molecule(
        self,
        filename_or_molecule: str | Molecule,
        charge: int | None = None,
        spin_multiplicity: int | None = None,
        tolerance: float = 0.01,
        allow_multiple_results: bool = False,
    ) -> list[str] | str:
        """Finds matching molecules from the Materials Project molecules database (MPcules).

        Multiple results may be returned of "similar" molecules based on
        distance using the pymatgen MoleculeMatcher algorithm.

        Args:
            filename_or_molecule: filename or Molecule object
            charge: Molecule charge. Default is None, meaning that the charge will not be used to
                restrict the output.
            spin_multiplicity: Molecule's spin multiplicity. Default is None, meaning that the output will
                not be restricted by spin multiplicity.
            tolerance: RMSD difference threshold for MoleculeMatcher
            allow_multiple_results: changes return type for either
            a single mpcule_id or list of mpcule_ids
        Returns:
            A matching mpcule_id if one is found or list of results if allow_multiple_results
            is True
        Raises:
            MPRestError
        """
        if isinstance(filename_or_molecule, str):
            m = Molecule.from_file(filename_or_molecule)
        elif isinstance(filename_or_molecule, Molecule):
            m = filename_or_molecule
        else:
            raise MPRestError("Provide filename or Structure object.")

        results = self._post_resource(
            body=m.as_dict(),
            params={
                "tolerance": tolerance,
                "charge": charge,
                "spin_multiplicity": spin_multiplicity,
            },
            suburl="find_molecule",
            use_document_model=False,
        ).get("data")

        if len(results) > 1:  # type: ignore
            if not allow_multiple_results:
                raise ValueError(
                    "Multiple matches found for this combination of tolerances, but "
                    "`allow_multiple_results` set to False."
                )
            return results  # type: ignore

        return results[0]["molecule_id"] if (results and results[0]) else []

    def search(
        self,
        charge: tuple[int, int] | None = None,
        spin_multiplicity: tuple[int, int] | None = None,
        nelements: tuple[int, int] | None = None,
        chemsys: str | list[str] | None = None,
        deprecated: bool | None = None,
        elements: list[str] | None = None,
        exclude_elements: list[str] | None = None,
        formula: str | list[str] | None = None,
        molecule_ids: MPculeID | list[MPculeID] | None = None,
        task_ids: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query molecule docs using a variety of search criteria.

        Arguments:
            charge (Tuple[int, int]): Minimum and maximum charge for the molecule.
            spin_multiplicity (Tuple[int, int]): Minimum and maximum spin for the molecule.
            nelements (Tuple[int, int]): Minimum and maximum number of elements
            chemsys (str, List[str]): A chemical system, list of chemical systems
                (e.g., Li-C-O, [C-O-H-N, Li-N]).
            deprecated (bool): Whether the material is tagged as deprecated.
            elements (List[str]): A list of elements.
            exclude_elements (List(str)): List of elements to exclude.
            formula (str, List[str]): An alphabetical formula or list of formulas
                (e.g. "C2 Li2 O4", ["C2 H4", "C2 H6"]).
            molecule_ids (MPculeID, List[MPculeID]): List of Materials Project Molecule IDs (MPculeIDs) to return data
                for.
            task_ids (str, List[str]): List of Materials Project IDs to return data for.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MoleculeDoc to return data for.
                Default is molecule_id, last_updated, and formula_alphabetical if all_fields is False.

        Returns:
            ([MoleculeDoc]) List of molecules documents
        """
        query_params: dict = {"deprecated": deprecated}

        if molecule_ids:
            if isinstance(molecule_ids, str):
                molecule_ids = [molecule_ids]

            query_params.update({"molecule_ids": ",".join(molecule_ids)})

        if charge:
            query_params.update({"charge": charge})

        if spin_multiplicity:
            query_params.update({"spin_multiplicity": spin_multiplicity})

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

        if task_ids:
            if isinstance(task_ids, str):
                task_ids = [task_ids]

            query_params.update({"task_ids": ",".join(validate_ids(task_ids))})

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


class AssociatedMoleculeRester(BaseMoleculeRester):
    suffix = "molecules/assoc"


class MoleculeRester(BaseMoleculeRester):
    suffix = "molecules/core"
    _sub_resters = MOLECULES_RESTERS
