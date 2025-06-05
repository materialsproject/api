from __future__ import annotations

import json
from collections import defaultdict

from monty.json import MontyDecoder
from emmet.core.phonon import PhononBSDOSDoc, PhononBS, PhononDOS

from mp_api.client.core import BaseRester, MPRestError
from mp_api.client.core.utils import validate_ids


class PhononRester(BaseRester[PhononBSDOSDoc]):
    suffix = "materials/phonon"
    document_model = PhononBSDOSDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: str | list[str] | None = None,
        phonon_method: str | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[PhononBSDOSDoc] | list[dict]:
        """Query phonon docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            phonon_method (str): phonon method to search (dfpt, phonopy, pheasy)
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in PhononBSDOSDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([PhononBSDOSDoc], [dict]) List of phonon documents or dictionaries.
        """
        query_params = defaultdict(dict)  # type: dict

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params["material_ids"] = ",".join(validate_ids(material_ids))

        if phonon_method and phonon_method in {"dfpt", "phonopy", "pheasy"}:
            query_params["phonon_method"] = phonon_method

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

    def get_bandstructure_from_material_id(self, material_id: str, phonon_method: str):
        """Get the phonon band structure pymatgen object associated with a given material ID and phonon method.

        Arguments:
            material_id (str): Material ID for the phonon band structure calculation
            phonon_method (str): phonon method, i.e. pheasy or dfpt

        Returns:
            bandstructure (PhononBS): PhononBS object
        """
        decoder = MontyDecoder().decode if self.monty_decode else json.loads
        result = self._query_open_data(
            bucket="materialsproject-parsed",
            key=f"ph-bandstructures/{phonon_method}/{material_id}.json.gz",
            decoder=decoder,
        )[0]

        if not result or not result[0]:
            raise MPRestError("No object found")

        if self.use_document_model:
            return PhononBS(**result[0])

        return result[0]

    def get_dos_from_material_id(self, material_id: str, phonon_method: str):
        """Get the phonon dos pymatgen object associated with a given material ID and phonon method.

        Arguments:
            material_id (str): Material ID for the phonon dos calculation
            phonon_method (str): phonon method, i.e. pheasy or dfpt

        Returns:
            dos (PhononDOS): PhononDOS object
        """
        decoder = MontyDecoder().decode if self.monty_decode else json.loads
        result = self._query_open_data(
            bucket="materialsproject-parsed",
            key=f"ph-dos/{phonon_method}/{material_id}.json.gz",
            decoder=decoder,
        )[0]

        if not result or not result[0]:
            raise MPRestError("No object found")

        if self.use_document_model:
            return PhononDOS(**result[0])

        return result[0]

    def get_forceconstants_from_material_id(self, material_id: str):
        """Get the force constants associated with a given material ID.

        Arguments:
            material_id (str): Material ID for the force constants calculation

        Returns:
            force constants (list[list[Matrix3D]]): PhononDOS object
        """
        decoder = MontyDecoder().decode if self.monty_decode else json.loads
        result = self._query_open_data(
            bucket="materialsproject-parsed",
            key=f"ph-force-constants/{material_id}.json.gz",
            decoder=decoder,
        )[0]

        if not result or not result[0]:
            raise MPRestError("No object found")

        return result[0]
