from __future__ import annotations

from emmet.core.molecules.vibration import VibrationDoc
from emmet.core.mpid import MPculeID

from mp_api.client.core import BaseRester


class MoleculesVibrationRester(BaseRester[VibrationDoc]):
    suffix = "molecules/vibrations"
    document_model = VibrationDoc
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
        num_chunks: int | None = None,
        sort_fields: list[str] | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query molecules vibration docs using a variety of search criteria.

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
            electronic_energy (Tuple[float, float]): Minimum and maximum electronic energy
            zero_point_energy (Tuple[float, float]): Minimum and maximum zero-point energy
            total_enthalpy (Tuple[float, float]): Minimum and maximum total enthalpy
            total_entropy (Tuple[float, float]): Minimum and maximum total entropy
            translational_enthalpy (Tuple[float, float]): Minimum and maximum translational enthalpy
            rotational_enthalpy (Tuple[float, float]): Minimum and maximum rotational enthalpy
            vibrational_enthalpy (Tuple[float, float]): Minimum and maximum vibrational enthalpy
            translational_entropy (Tuple[float, float]): Minimum and maximum translational enthalpy
            rotational_entropy (Tuple[float, float]): Minimum and maximum rotational enthalpy
            vibrational_entropy (Tuple[float, float]): Minimum and maximum vibrational enthalpy
            free_energy (Tuple[float, float]): Minimum and maximum free energy
            formula (str, List[str]): An alphabetical formula or list of formulas
                (e.g. "C2 Li2 O4", ["C2 H4", "C2 H6"]).
            elements (List[str]): A list of elements.
            exclude_elements (List(str)): List of elements to exclude.
            chemsys (str, List[str]): A chemical system, list of chemical systems
                (e.g., Li-C-O, [C-O-H-N, Li-N]), or single formula (e.g., C2 H4).
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in MoleculeDoc to return data for.
                Default is "molecule_id", "property_id", "solvent", "method", "last_updated"
                if all_fields is False.

        Returns:
            ([VibrationDoc]) List of molecule vibration documents
        """
        query_params = {}  # type: dict

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

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
