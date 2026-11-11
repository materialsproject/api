from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING

from emmet.core.band_theory import BSPathType
from emmet.core.mpid import AlphaID
from emmet.core.phonon import PhononBS, PhononBSDOSDoc, PhononBSDOSTask, PhononDOS

from mp_api.client.core import BaseRester, MPRestError
from mp_api.client.core._display import status
from mp_api.client.core.utils import validate_ids
from mp_api.client.routes.materials.summary import SummaryRester

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Literal

    from emmet.core.math import Matrix3D

logger = logging.getLogger(__name__)

# Order in which phonon methods are tried when the caller doesn't pick one
_METHOD_PREFERENCE = ("pheasy", "dfpt")


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
                delta_catalog=self.delta_catalog,
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
            identifiers (str | list[str]): A single Phonon Task ID string or list of strings
                (e.g., aaaaaaft, [aaaaaaft, aaaeguxu]).
            material_ids (str | list[str]): A single Materials Project ID or list of IDs
                (e.g., mp-149, [mp-149, mp-13]).
            phonon_method (str): phonon method to search (dfpt, phonopy, pheasy)
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (list[str]): List of fields in PhononBSDOSTask to return data for.
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
                mid = str(doc["material_id"])  # type: ignore[arg-type, index]
                phonon_ids_by_method = doc.get("phonon_IDs") or {}  # type: ignore[union-attr]

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

    def _unsupported(
        self,
        phonon_method: str,
        what: str,
        path_type: BSPathType | None = None,
    ) -> str | None:
        """Why `phonon_method` can't have this kind of data, or None if it can.

        Known from how the data is produced, so no query is needed:
        dfpt band structures only exist for the Setyawan-Curtarolo path, and
        only pheasy produces force constants.

        Args:
            phonon_method (str) : phonon method
            what (str) : kind of data: "band structure", "DOS" or "force constants"
            path_type (BSPathType or None) : k-path of a band structure
        """
        if (
            what == "band structure"
            and phonon_method == "dfpt"
            and path_type not in (None, BSPathType.setyawan_curtarolo)
        ):
            return (
                "dfpt phonon band structures are only available with "
                f'path_type="{BSPathType.setyawan_curtarolo.value}".'
            )
        if what == "force constants" and phonon_method != "pheasy":
            return (
                f"{phonon_method} phonon calculations have no force constants; "
                'use phonon_method="pheasy".'
            )
        return None

    def _phonon_candidates(
        self,
        material_id: str,
        what: str,
        phonon_method: str | None = None,
        path_type: BSPathType | None = None,
    ) -> list[tuple[str, str]]:
        """The phonon calculations of a material to take `what` from, in order.

        With `phonon_method` unset, every method the material has data for that
        can provide `what`, pheasy first, then dfpt. With it set, only that one:
        an explicitly requested method is never replaced by another.

        Args:
            material_id (str) : Materials Project ID
            what (str) : kind of data: "band structure", "DOS" or "force constants"
            phonon_method (str or None) : phonon method, None to choose
            path_type (BSPathType or None) : k-path of a band structure

        Returns:
            list of (phonon method, phonon ID)

        Raises:
            MPRestError: if the material has no suitable phonon data.
        """
        if phonon_method and (
            reason := self._unsupported(phonon_method, what, path_type)
        ):
            raise MPRestError(reason)

        summary_doc = self.summary_rester.search(
            material_ids=material_id, fields=["phonon_IDs"]
        )
        phonon_ids = (summary_doc[0].get("phonon_IDs") if summary_doc else None) or {}  # type: ignore[union-attr]
        available = {method: ids for method, ids in phonon_ids.items() if ids}
        if not available:
            raise MPRestError(f"No phonon data found for material ID {material_id}.")

        if phonon_method:
            if phonon_method not in available:
                raise MPRestError(
                    f"No {phonon_method} phonon data for {material_id} "
                    f"(available: {', '.join(sorted(available))}). Pass "
                    f'phonon_method="{sorted(available)[0]}", or leave it unset '
                    "to choose automatically."
                )
            methods = [phonon_method]
        else:
            methods = [m for m in _METHOD_PREFERENCE if m in available] + sorted(
                m for m in available if m not in _METHOD_PREFERENCE
            )
            reasons = {m: self._unsupported(m, what, path_type) for m in methods}
            if not (usable := [m for m in methods if not reasons[m]]):
                raise MPRestError(
                    f"No phonon {what} available for {material_id}: "
                    + " ".join(r for r in reasons.values() if r)
                )
            methods = usable

        logger.debug(
            f"Using {methods[0]} phonon data for {material_id} "
            f"(available: {', '.join(sorted(available))})"
        )
        return [(method, available[method][0]) for method in methods]

    @staticmethod
    def _first_available(
        candidates: list[tuple[str, str]],
        fetch: Callable[[str, str], Any],
        what: str,
        material_id: str,
    ) -> tuple[str, str, Any]:
        """Fetch `what` from the first candidate that has it.

        Falls through to the next candidate when a calculation has no such
        data, and says so, since the data then comes from another method
        than usual.

        Args:
            candidates (list of tuple) : (phonon method, phonon ID), see `_phonon_candidates`
            fetch (callable) : `fetch(phonon_id, phonon_method)`, None if there's no data
            what (str) : kind of data, for messages
            material_id (str) : Materials Project ID, for messages

        Returns:
            tuple of the phonon method, the phonon ID and the data

        Raises:
            MPRestError: if no candidate has the data.
        """
        for method, phonon_id in candidates:
            if (data := fetch(phonon_id, method)) is not None:
                if (first := candidates[0])[0] != method:
                    logger.warning(
                        f"No {first[0]} phonon {what} for {material_id} ({first[1]}), "
                        f"using {method} ({phonon_id}) instead."
                    )
                return method, phonon_id, data
        tried = ", ".join(f"{m} {i}" for m, i in candidates)
        raise MPRestError(f"No phonon {what} found for {material_id} (tried {tried}).")

    def _fetch_bandstructure(
        self,
        identifier: str,
        phonon_method: str,
        path_type: str | BSPathType | None,
    ) -> PhononBS | dict[str, Any] | None:
        """The band structure, or None if there is none for this calculation."""
        ph_bs_lbl, _ = self._get_delta_table(
            "materialsproject-parsed",
            "phonon/electronic-structure/bandstructures/",
            label="ph_bandstructure",
        )

        query = f"""
            SELECT *
            FROM   {ph_bs_lbl}
            WHERE  identifier='{str(AlphaID(identifier.split("-")[-1], padlen=8))}'
            AND    phonon_method='{phonon_method}'
        """

        if path_type:
            query += f"\nAND path_convention='{path_type}'"

        table = self._query_delta_single(query, label=ph_bs_lbl)
        deser = table.to_pylist(maps_as_pydicts="strict")
        if deser and deser[0].get("bandstructure") is not None:
            bs = deser[0]["bandstructure"]
            return PhononBS(**bs) if self.use_document_model else bs
        return None

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
                dfpt band structures only exist for setyawan_curtarolo.

        Returns:
            bandstructure (PhononBS): PhononBS object
        """
        with status(
            f"Fetching the {phonon_method} phonon band structure for {identifier}...",
            enabled=not self.mute_progress_bars,
        ):
            bs = self._fetch_bandstructure(identifier, phonon_method, path_type)
        if bs is None:
            raise MPRestError(
                f"No phonon bandstructure data found for {identifier=} and {phonon_method=}"
                + (f" and path_type={path_type}" if path_type else "")
            )
        return bs

    def get_bandstructure_from_material_id(
        self,
        material_id: str,
        phonon_method: Literal["pheasy", "dfpt"] | None = None,
        path_type: str | BSPathType = BSPathType.setyawan_curtarolo,
    ) -> PhononBS | dict[str, Any]:
        """Get the phonon band structure pymatgen object associated with a given material ID.

        Arguments:
            material_id (str): Materials Project ID for a material
            phonon_method (str or None): phonon method, i.e. pheasy or dfpt. By default,
                the method is chosen from the material's data: pheasy if it has it,
                otherwise dfpt. If the pheasy calculation has no band structure,
                the dfpt one is used (with a warning). A method passed explicitly
                is never replaced.
            path_type (BSPathType or str): k-path selection convention for the band structure.
                pheasy has all conventions; dfpt only has setyawan_curtarolo.

        Returns:
            bandstructure (PhononBS): PhononBS object

        Raises:
            MPRestError: if there's no suitable data. The message names the
                methods the material does have data for.
        """
        pt = BSPathType(path_type) if isinstance(path_type, str) else path_type
        with status(
            f"Fetching the phonon band structure for {material_id}...",
            enabled=not self.mute_progress_bars,
        ):
            candidates = self._phonon_candidates(
                material_id, "band structure", phonon_method, pt
            )
            _, _, bs = self._first_available(
                candidates,
                lambda pid, method: self._fetch_bandstructure(pid, method, pt),
                "band structure",
                material_id,
            )
        return bs

    def _fetch_dos(
        self, identifier: str, phonon_method: str
    ) -> PhononDOS | dict[str, Any] | None:
        """The DOS, or None if there is none for this calculation."""
        ph_dos_lbl, _ = self._get_delta_table(
            "materialsproject-parsed",
            "phonon/electronic-structure/dos/",
            label="ph_dos",
        )

        query = f"""
            SELECT *
            FROM   {ph_dos_lbl}
            WHERE  identifier='{str(AlphaID(identifier.split("-")[-1], padlen=8))}'
            AND    phonon_method='{phonon_method}'
        """

        table = self._query_delta_single(query, label=ph_dos_lbl)
        deser = table.to_pylist(maps_as_pydicts="strict")
        if deser and deser[0].get("dos") is not None:
            dos = deser[0]["dos"]
            return PhononDOS(**dos) if self.use_document_model else dos
        return None

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
        with status(
            f"Fetching the {phonon_method} phonon DOS for {identifier}...",
            enabled=not self.mute_progress_bars,
        ):
            dos = self._fetch_dos(identifier, phonon_method)
        if dos is None:
            raise MPRestError(
                f"No phonon dos data found for {identifier=} and {phonon_method=}"
            )
        return dos

    def get_dos_from_material_id(
        self,
        material_id: str,
        phonon_method: Literal["pheasy", "dfpt"] | None = None,
    ) -> PhononDOS | dict[str, Any]:
        """Get the phonon dos pymatgen object associated with a given material ID.

        Arguments:
            material_id (str): Materials Project ID for a material
            phonon_method (str or None): phonon method, i.e. pheasy or dfpt. By default,
                the method is chosen from the material's data: pheasy if it has it,
                otherwise dfpt. If the pheasy calculation has no DOS, the dfpt one
                is used (with a warning). A method passed explicitly is never replaced.

        Returns:
            dos (PhononDOS): PhononDOS object

        Raises:
            MPRestError: if there's no suitable data. The message names the
                methods the material does have data for.
        """
        with status(
            f"Fetching the phonon DOS for {material_id}...",
            enabled=not self.mute_progress_bars,
        ):
            candidates = self._phonon_candidates(material_id, "DOS", phonon_method)
            _, _, dos = self._first_available(
                candidates, self._fetch_dos, "DOS", material_id
            )
        return dos

    def _fetch_forceconstants(
        self, identifier: str, phonon_method: str
    ) -> list[list[Matrix3D]] | None:
        """The force constants, or None if there are none for this calculation."""
        ph_fc_lbl, _ = self._get_delta_table(
            "materialsproject-parsed",
            "phonon/force-constants/",
            label="ph_force_constants",
        )

        query = f"""
            SELECT *
            FROM   {ph_fc_lbl}
            WHERE  identifier='{str(AlphaID(identifier.split("-")[-1], padlen=8))}'
            AND    phonon_method='{phonon_method}'
        """

        table = self._query_delta_single(query, label=ph_fc_lbl)
        deser = table.to_pylist(maps_as_pydicts="strict")
        if deser and deser[0].get("force_constants") is not None:
            return deser[0]["force_constants"]
        return None

    def get_forceconstants_from_phonon_id(
        self, identifier: str, phonon_method: str
    ) -> list[list[Matrix3D]]:
        """Get the force constants associated with a given phonon ID and phonon method.

        Arguments:
            identifier (str): Phonon ID for the force constants calculation
            phonon_method (str): phonon method. Only pheasy calculations have force constants.

        Returns:
            force constants (list[list[Matrix3D]]): force constants
        """
        with status(
            f"Fetching the {phonon_method} force constants for {identifier}...",
            enabled=not self.mute_progress_bars,
        ):
            fcs = self._fetch_forceconstants(identifier, phonon_method)
        if fcs is None:
            raise MPRestError(
                f"No phonon force constants data found for {identifier=} and {phonon_method=}"
            )
        return fcs

    def get_forceconstants_from_material_id(
        self, material_id: str, phonon_method: str
    ) -> list[list[Matrix3D]]:
        """Get the force constants associated with a given material ID and phonon method.

        Arguments:
            material_id (str): Materials Project ID for a material
            phonon_method (str): phonon method. Only pheasy calculations have
                force constants; passing dfpt raises an error.

        Returns:
            force constants (list[list[Matrix3D]]): force constants

        Raises:
            MPRestError: if the method can't have force constants, or the
                material has none.
        """
        with status(
            f"Fetching the {phonon_method} force constants for {material_id}...",
            enabled=not self.mute_progress_bars,
        ):
            candidates = self._phonon_candidates(
                material_id, "force constants", phonon_method
            )
            _, _, fcs = self._first_available(
                candidates, self._fetch_forceconstants, "force constants", material_id
            )
        return fcs

    def compute_thermo_quantities(
        self,
        material_id: str | None = None,
        phonon_method: Literal["pheasy", "dfpt"] | None = None,
        identifier: str | None = None,
    ):
        """Compute thermodynamical quantities for a given phonon ID or material ID and phonon_method.

        Exactly one of `identifier` or `material_id` must be supplied.

        Arguments:
            identifier (str): Phonon ID to calculate quantities for. Requires `phonon_method`.
            material_id (str): Materials Project ID to calculate quantities for.
            phonon_method (str): phonon method, i.e. pheasy or dfpt. With `material_id`,
                the method is chosen from the material's data (pheasy, then dfpt)
                unless given; the first phonon ID of the method is used.

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
            with status(
                f"Computing thermodynamic quantities for {material_id or identifier}...",
                enabled=not self.mute_progress_bars,
            ):
                if material_id:
                    candidates = self._phonon_candidates(
                        material_id, "DOS", phonon_method
                    )
                    phonon_method_used, identifier, ph_dos = self._first_available(
                        candidates, self._fetch_dos, "DOS", material_id
                    )
                    phonon_method = phonon_method_used  # type: ignore[assignment]
                else:
                    if identifier is None or phonon_method is None:
                        raise MPRestError(
                            f"Could not resolve a phonon identifier or method "
                            f"for {identifier=} ({phonon_method=})."
                        )
                    ph_dos = self.get_dos_from_phonon_id(identifier, phonon_method)

                docs = self.search(identifiers=identifier, phonon_method=phonon_method)
                if not docs or not docs[0]:
                    raise MPRestError("No phonon document found")

                self.use_document_model = True
                docs[0]["phonon_dos"] = ph_dos  # type: ignore[index]
                doc = PhononBSDOSDoc(**docs[0])  # type: ignore[arg-type, index]
        finally:
            self.use_document_model = use_document_model
        # below: same as numpy.linspace(0,800,100) but written out for mypy
        return doc.compute_thermo_quantities([i * 800 / 99 for i in range(100)])
