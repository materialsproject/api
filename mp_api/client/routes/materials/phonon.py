from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from emmet.core.band_theory import BSPathType
from emmet.core.mpid import AlphaID
from emmet.core.phonon import PhononBS, PhononBSDOSDoc, PhononBSDOSTask, PhononDOS

from mp_api.client.core import BaseRester, MPRestError
from mp_api.client.core.utils import validate_ids
from mp_api.client.routes.materials.summary import SummaryRester

if TYPE_CHECKING:
    from typing import Any

    from emmet.core.math import Matrix3D


class PhononRester(BaseRester):
    _summary_rester: SummaryRester | None = None
    suffix = "materials/phonon"
    document_model = PhononBSDOSTask  # type: ignore
    primary_key = "identifier"

    @property
    def summary_rester(self) -> SummaryRester:
        if not self._summary_rester:
            self._summary_rester = SummaryRester(
                api_key=self.api_key,
                endpoint=self.base_endpoint,
                include_user_agent=self.include_user_agent,
                session=self.session,
                use_document_model=self.use_document_model,
                headers=self.headers,
                mute_progress_bars=self.mute_progress_bars,
            )
        return self._summary_rester

    def search(
        self,
        identifiers: str | list[str] | None = None,
        material_ids: str | list[str] | None = None,
        phonon_method: str | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[PhononBSDOSTask] | list[dict]:
        """Query phonon docs using a variety of search criteria.

        Exactly one of `identifiers` and `material_ids` may be supplied.
        When `material_ids` is supplied, the summary endpoint is queried to
        resolve each material's `phonon_IDs` into the underlying phonon task
        identifiers (filtered by `phonon_method` when provided), and those
        phonon IDs are then used to query the phonon endpoint.

        Arguments:
            identifiers (str, List[str]): A single Phonon Task ID string or list of strings
                (e.g., aaaaaaft, [aaaaaaft, aaaeguxu]).
            material_ids (str, List[str]): A single Materials Project ID or list of IDs
                (e.g., mp-149, [mp-149, mp-13]).
            phonon_method (str): phonon method to search (dfpt, phonopy, pheasy)
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in PhononBSDOSTask to return data for.
                Default is identifier, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([PhononBSDOSTask], [dict]) List of phonon documents or dictionaries.
        """
        if identifiers and material_ids:
            raise MPRestError(
                "Specify exactly one of `identifiers` or `material_ids`, not both."
            )

        query_params: dict = defaultdict(dict)

        if material_ids:
            material_ids = (
                [material_ids] if isinstance(material_ids, str) else list(material_ids)
            )
            summary_docs = self.summary_rester.search(
                material_ids=material_ids, fields=["material_id", "phonon_IDs"]
            )

            resolved_ids: list[str] = []
            missing: list[str] = []
            found_material_ids: set[str] = set()
            for doc in summary_docs:
                mid = str(doc["material_id"])
                phonon_ids_by_method = doc.get("phonon_IDs") or {}

                if phonon_method:
                    method_ids = phonon_ids_by_method.get(phonon_method) or []
                else:
                    method_ids = [
                        pid for ids in phonon_ids_by_method.values() for pid in ids
                    ]

                if not method_ids:
                    missing.append(mid)
                    continue

                found_material_ids.add(mid)
                resolved_ids.extend(method_ids)

            missing.extend(mid for mid in material_ids if mid not in found_material_ids)

            if missing:
                method_suffix = (
                    f" with phonon_method={phonon_method!r}" if phonon_method else ""
                )
                raise MPRestError(
                    f"No phonon data found for material ID(s) {sorted(set(missing))}"
                    f"{method_suffix}."
                )

            identifiers = resolved_ids

        if identifiers:
            query_params["identifiers"] = ",".join(
                validate_ids(
                    [identifiers] if isinstance(identifiers, str) else identifiers
                )
            )

        if phonon_method and phonon_method in {"dfpt", "phonopy", "pheasy"}:
            query_params["phonon_method"] = phonon_method

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super()._search(  # type: ignore[return-value]
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )

    def get_bandstructure_from_phonon_id(
        self,
        identifier: str,
        phonon_method: str,
        path_type: str | BSPathType = BSPathType.setyawan_curtarolo,
    ) -> PhononBS | dict[str, Any]:
        """Get the phonon band structure pymatgen object associated with a given phonon ID and phonon method.

        Arguments:
            identifier (str): Phonon ID for the phonon band structure calculation
            phonon_method (str): phonon method, i.e. pheasy or dfpt
            path_type (BSPathType or str): k-path selection convention for the band structure.

        Returns:
            bandstructure (PhononBS): PhononBS object
        """
        ph_bs_lbl, _ = self._get_delta_table(
            "materialsproject-parsed",
            "phonon/electronic-structure/bandstructures/",
            label="ph_bandstructure",
        )

        query = f"""
            SELECT *
            FROM   {ph_bs_lbl}
            WHERE  identifier='{str(AlphaID(identifier.split("-")[-1],padlen=8))}'
            AND    phonon_method='{phonon_method}'
        """

        if path_type:
            query += f"\nAND path_convention='{path_type}'"

        table = self._query_delta_single(query)
        deser = table.to_pylist(maps_as_pydicts="strict")
        if deser and deser[0].get("bandstructure") is not None:
            bs = deser[0]["bandstructure"]
            return PhononBS(**bs) if self.use_document_model else bs

        raise MPRestError(
            f"No phonon bandstructure data found for {identifier=} and {phonon_method=}"
            + (f" and run_type={path_type}" if path_type else "")
        )

    def get_bandstructure_from_material_id(
        self,
        material_id: str,
        phonon_method: str,
        path_type: str | BSPathType = BSPathType.setyawan_curtarolo,
    ) -> PhononBS | dict[str, Any]:
        """Get the phonon band structure pymatgen object associated with a given material ID and phonon method.

        Arguments:
            material_id (str): Materials Project ID for a material
            phonon_method (str): phonon method, i.e. pheasy or dfpt
            path_type (BSPathType or str): k-path selection convention for the band structure.

        Returns:
            bandstructure (PhononBS): PhononBS object
        """
        pt: BSPathType = (
            BSPathType(path_type) if isinstance(path_type, str) else path_type
        )

        if not (
            summary_doc := self.summary_rester.search(
                material_ids=material_id, fields=["phonon_IDs"]
            )
        ):
            raise MPRestError(
                f"No phonon bandstructure data found for material ID {material_id}."
            )

        if phonon_method not in summary_doc[0]["phonon_IDs"]:
            raise MPRestError(
                f"No phonon bandstructure data found for material ID: {material_id} and phonon method: {phonon_method}."
            )

        return self.get_bandstructure_from_phonon_id(
            summary_doc[0]["phonon_IDs"][phonon_method][0], phonon_method, pt
        )

    def get_dos_from_phonon_id(
        self, identifier: str, phonon_method: str
    ) -> PhononDOS | dict[str, Any]:
        """Get the phonon dos pymatgen object associated with a given phonon ID and phonon method.

        Arguments:
            identifier (str): Phonon ID for the phonon dos calculation
            phonon_method (str): phonon method, i.e. pheasy or dfpt

        Returns:
            dos (PhononDOS): PhononDOS object
        """
        ph_dos_lbl, _ = self._get_delta_table(
            "materialsproject-parsed",
            "phonon/electronic-structure/dos/",
            label="ph_dos",
        )

        query = f"""
            SELECT *
            FROM   {ph_dos_lbl}
            WHERE  identifier='{str(AlphaID(identifier.split("-")[-1],padlen=8))}'
            AND    phonon_method='{phonon_method}'
        """

        table = self._query_delta_single(query)
        deser = table.to_pylist(maps_as_pydicts="strict")
        if deser and deser[0].get("dos") is not None:
            dos = deser[0]["dos"]
            return PhononDOS(**dos) if self.use_document_model else dos

        raise MPRestError(
            f"No phonon dos data found for {identifier=} and {phonon_method=}"
        )

    def get_dos_from_material_id(
        self, material_id: str, phonon_method: str
    ) -> PhononDOS | dict[str, Any]:
        """Get the phonon dos pymatgen object associated with a given material ID and phonon method.

        Arguments:
            material_id (str): Materials Project ID for a material
            phonon_method (str): phonon method, i.e. pheasy or dfpt

        Returns:
            dos (PhononDOS): PhononDOS object
        """
        if not (
            summary_doc := self.summary_rester.search(
                material_ids=material_id, fields=["phonon_IDs"]
            )
        ):
            raise MPRestError(
                f"No phonon dos data found for material ID {material_id}."
            )

        if phonon_method not in summary_doc[0]["phonon_IDs"]:
            raise MPRestError(
                f"No phonon dos data found for material ID: {material_id} and phonon method: {phonon_method}."
            )

        return self.get_dos_from_phonon_id(
            summary_doc[0]["phonon_IDs"][phonon_method][0], phonon_method
        )

    def get_forceconstants_from_phonon_id(
        self, identifier: str, phonon_method: str
    ) -> list[list[Matrix3D]]:
        """Get the force constants associated with a given phonon ID and phonon method.

        Arguments:
            identifier (str): Phonon ID for the force constants calculation
            phonon_method (str): phonon method, i.e. pheasy or dfpt

        Returns:
            force constants (list[list[Matrix3D]]): force constants
        """
        ph_fc_lbl, _ = self._get_delta_table(
            "materialsproject-parsed",
            "phonon/force-constants/",
            label="ph_force_constants",
        )

        query = f"""
            SELECT *
            FROM   {ph_fc_lbl}
            WHERE  identifier='{str(AlphaID(identifier.split("-")[-1],padlen=8))}'
            AND    phonon_method='{phonon_method}'
        """

        table = self._query_delta_single(query)
        deser = table.to_pylist(maps_as_pydicts="strict")
        if deser and deser[0].get("force_constants") is not None:
            return deser[0]["force_constants"]

        raise MPRestError(
            f"No phonon force constants data found for {identifier=} and {phonon_method=}"
        )

    def get_forceconstants_from_material_id(
        self, material_id: str, phonon_method: str
    ) -> list[list[Matrix3D]]:
        """Get the force constants associated with a given material ID and phonon method.

        Arguments:
            material_id (str): Materials Project ID for a material
            phonon_method (str): phonon method, i.e. pheasy or dfpt

        Returns:
            force constants (list[list[Matrix3D]]): force constants
        """
        if not (
            summary_doc := self.summary_rester.search(
                material_ids=material_id, fields=["phonon_IDs"]
            )
        ):
            raise MPRestError(
                f"No phonon force constants data found for material ID {material_id}."
            )

        if phonon_method not in summary_doc[0]["phonon_IDs"]:
            raise MPRestError(
                f"No phonon force constants data found for material ID: {material_id} and phonon method: {phonon_method}."
            )

        return self.get_forceconstants_from_phonon_id(
            summary_doc[0]["phonon_IDs"][phonon_method][0], phonon_method
        )

    def compute_thermo_quantities(
        self,
        identifier: str | None = None,
        material_id: str | None = None,
        phonon_method: str | None = None,
    ):
        """Compute thermodynamical quantities for a given phonon ID or material ID and phonon_method.

        Exactly one of `identifier` or `material_id` must be supplied.

        Arguments:
            identifier (str): Phonon ID to calculate quantities for
            material_id (str): Materials Project ID to calculate quantities for; the first
                phonon ID associated with the requested `phonon_method` for the material
                will be used.
            phonon_method (str): phonon method, i.e. pheasy or dfpt

        Returns:
            quantities (dict): thermodynamical quantities
        """
        if identifier and material_id:
            raise MPRestError(
                "Specify exactly one of `identifier` or `material_id`, not both."
            )
        if not identifier and not material_id:
            raise MPRestError("One of `identifier` or `material_id` must be specified.")

        use_document_model = self.use_document_model
        self.use_document_model = False
        try:
            if material_id:
                if not (
                    summary_doc := self.summary_rester.search(
                        material_ids=material_id, fields=["phonon_IDs"]
                    )
                ):
                    raise MPRestError(
                        f"No phonon data found for material ID {material_id}."
                    )
                if phonon_method not in summary_doc[0]["phonon_IDs"]:
                    raise MPRestError(
                        f"No phonon data found for material ID: {material_id} and "
                        f"phonon method: {phonon_method}."
                    )
                identifier = summary_doc[0]["phonon_IDs"][phonon_method][0]

            ph_dos = self.get_dos_from_phonon_id(identifier, phonon_method)
            docs = self.search(identifiers=identifier, phonon_method=phonon_method)
            if not docs or not docs[0]:
                raise MPRestError("No phonon document found")

            self.use_document_model = True
            docs[0]["phonon_dos"] = ph_dos  # type: ignore[index]
            doc = PhononBSDOSDoc(**docs[0])  # type: ignore[arg-type]
        finally:
            self.use_document_model = use_document_model
        # below: same as numpy.linspace(0,800,100) but written out for mypy
        return doc.compute_thermo_quantities([i * 800 / 99 for i in range(100)])
