from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

import numpy as np
from emmet.core.phonon import PhononBS, PhononBSDOSDoc, PhononDOS

from mp_api.client.core import BaseRester, MPRestError
from mp_api.client.core.utils import validate_ids

if TYPE_CHECKING:
    from typing import Any

    from emmet.core.math import Matrix3D


class PhononRester(BaseRester):
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
        query_params: dict = defaultdict(dict)

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

    def get_bandstructure_from_material_id(
        self, material_id: str, phonon_method: str
    ) -> PhononBS | dict[str, Any]:
        """Get the phonon band structure pymatgen object associated with a given material ID and phonon method.

        Arguments:
            material_id (str): Material ID for the phonon band structure calculation
            phonon_method (str): phonon method, i.e. pheasy or dfpt

        Returns:
            bandstructure (PhononBS): PhononBS object
        """
        result = self._query_open_data(
            bucket="materialsproject-parsed",
            key=f"ph-bandstructures/{phonon_method}/{material_id}.json.gz",
        )[0][0]

        if self.use_document_model:
            return PhononBS(**result)

        return result

    def get_dos_from_material_id(
        self, material_id: str, phonon_method: str
    ) -> PhononDOS | dict[str, Any]:
        """Get the phonon dos pymatgen object associated with a given material ID and phonon method.

        Arguments:
            material_id (str): Material ID for the phonon dos calculation
            phonon_method (str): phonon method, i.e. pheasy or dfpt

        Returns:
            dos (PhononDOS): PhononDOS object
        """
        result = self._query_open_data(
            bucket="materialsproject-parsed",
            key=f"ph-dos/{phonon_method}/{material_id}.json.gz",
        )[0][0]

        if self.use_document_model:
            return PhononDOS(**result)

        return result

    def get_forceconstants_from_material_id(
        self, material_id: str
    ) -> list[list[Matrix3D]]:
        """Get the force constants associated with a given material ID.

        Arguments:
            material_id (str): Material ID for the force constants calculation

        Returns:
            force constants (list[list[Matrix3D]]): PhononDOS object
        """
        return self._query_open_data(
            bucket="materialsproject-parsed",
            key=f"ph-force-constants/{material_id}.json.gz",
        )[0][0]

    def compute_thermo_quantities(self, material_id: str, phonon_method: str):
        """Compute thermodynamical quantities for given material ID and phonon_method.

        Arguments:
            material_id (str): Material ID to calculate quantities for
            phonon_method (str): phonon method, i.e. pheasy or dfpt

        Returns:
            quantities (dict): thermodynamical quantities
        """
        use_document_model = self.use_document_model
        self.use_document_model = False
        docs = self.search(material_ids=material_id, phonon_method=phonon_method)
        if not docs or not docs[0]:
            raise MPRestError("No phonon document found")

        self.use_document_model = True
        docs[0]["phonon_dos"] = self.get_dos_from_material_id(
            material_id, phonon_method
        )
        doc = PhononBSDOSDoc(**docs[0])
        self.use_document_model = use_document_model
        return doc.compute_thermo_quantities(np.linspace(0, 800, 100))
