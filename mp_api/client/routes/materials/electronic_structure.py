from __future__ import annotations

import warnings
from collections import defaultdict
from typing import TYPE_CHECKING

from emmet.core.electronic_structure import (
    BSPathType,
    DOSProjectionType,
    ElectronicStructureDoc,
)
from pymatgen.analysis.magnetism.analyzer import Ordering
from pymatgen.core.periodic_table import Element
from pymatgen.electronic_structure.core import OrbitalType, Spin

from mp_api.client.core import BaseRester, MPRestError
from mp_api.client.core.utils import load_json, validate_ids

if TYPE_CHECKING:
    from pymatgen.electronic_structure.dos import CompleteDos


class ElectronicStructureRester(BaseRester):
    suffix = "materials/electronic_structure"
    document_model = ElectronicStructureDoc  # type: ignore
    primary_key = "material_id"

    def search_electronic_structure_docs(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "MPRester.electronic_structure.search_electronic_structure_docs is deprecated. "
            "Please use MPRester.electronic_structure.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
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
    ):
        """Query electronic structure docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            band_gap (Tuple[float,float]): Minimum and maximum band gap in eV to consider.
            chemsys (str, List[str]): A chemical system or list of chemical systems
                (e.g., Li-Fe-O, Si-*, [Si-O, Li-Fe-P]).
            efermi (Tuple[float,float]): Minimum and maximum fermi energy in eV to consider.
            elements (List[str]): A list of elements.
            exclude_elements (List[str]): A list of elements to exclude.
            formula (str, List[str]): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*). A list of chemical formulas can also be passed
                (e.g., [Fe2O3, ABO3]).
            is_gap_direct (bool): Whether the material has a direct band gap.
            is_metal (bool): Whether the material is considered a metal.
            magnetic_ordering (Ordering): Magnetic ordering of the material.
            num_elements (Tuple[int,int]): Minimum and maximum number of elements to consider.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in ElectronicStructureDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([ElectronicStructureDoc]) List of electronic structure documents
        """
        query_params: dict = defaultdict(dict)

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

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

        if band_gap:
            query_params.update(
                {"band_gap_min": band_gap[0], "band_gap_max": band_gap[1]}
            )

        if efermi:
            query_params.update({"efermi_min": efermi[0], "efermi_max": efermi[1]})

        if magnetic_ordering:
            query_params.update({"magnetic_ordering": magnetic_ordering.value})

        if num_elements:
            if isinstance(num_elements, int):
                num_elements = (num_elements, num_elements)
            query_params.update(
                {"nelements_min": num_elements[0], "nelements_max": num_elements[1]}
            )

        if is_gap_direct is not None:
            query_params.update({"is_gap_direct": is_gap_direct})

        if is_metal is not None:
            query_params.update({"is_metal": is_metal})

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


class BaseESPropertyRester(BaseRester):
    _es_rester: ElectronicStructureRester | None = None
    document_model = ElectronicStructureDoc

    @property
    def es_rester(self) -> ElectronicStructureRester:
        if not self._es_rester:
            self._es_rester = ElectronicStructureRester(
                api_key=self.api_key,
                endpoint=self.base_endpoint,
                include_user_agent=self.include_user_agent,
                session=self.session,
                use_document_model=self.use_document_model,
                headers=self.headers,
                mute_progress_bars=self.mute_progress_bars,
            )
        return self._es_rester


class BandStructureRester(BaseESPropertyRester):
    suffix = "materials/electronic_structure/bandstructure"

    def search_bandstructure_summary(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "MPRester.electronic_structure_bandstructure.search_bandstructure_summary is deprecated. "
            "Please use MPRester.electronic_structure_bandstructure.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        band_gap: tuple[float, float] | None = None,
        efermi: tuple[float, float] | None = None,
        is_gap_direct: bool | None = None,
        is_metal: bool | None = None,
        magnetic_ordering: Ordering | str | None = None,
        path_type: BSPathType | str = BSPathType.setyawan_curtarolo,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query band structure summary data in electronic structure docs using a variety of search criteria.

        Arguments:
            band_gap (Tuple[float,float]): Minimum and maximum band gap in eV to consider.
            efermi (Tuple[float,float]): Minimum and maximum fermi energy in eV to consider.
            is_gap_direct (bool): Whether the material has a direct band gap.
            is_metal (bool): Whether the material is considered a metal.
            magnetic_ordering (Ordering or str): Magnetic ordering of the material.
            path_type (BSPathType or str): k-path selection convention for the band structure.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in ElectronicStructureDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([ElectronicStructureDoc]) List of electronic structure documents
        """
        query_params: dict = defaultdict(dict)

        query_params["path_type"] = (
            BSPathType[path_type] if isinstance(path_type, str) else path_type
        ).value

        if band_gap:
            query_params.update(
                {"band_gap_min": band_gap[0], "band_gap_max": band_gap[1]}
            )

        if efermi:
            query_params.update({"efermi_min": efermi[0], "efermi_max": efermi[1]})

        if magnetic_ordering:
            query_params.update(
                {
                    "magnetic_ordering": (
                        Ordering(magnetic_ordering)
                        if isinstance(magnetic_ordering, str)
                        else magnetic_ordering
                    ).value
                }
            )

        if is_gap_direct is not None:
            query_params.update({"is_gap_direct": is_gap_direct})

        if is_metal is not None:
            query_params.update({"is_metal": is_metal})

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

    def get_bandstructure_from_task_id(self, task_id: str):
        """Get the band structure pymatgen object associated with a given task ID.

        Arguments:
            task_id (str): Task ID for the band structure calculation

        Returns:
            bandstructure (BandStructure): BandStructure or BandStructureSymmLine object
        """
        return self._query_open_data(
            bucket="materialsproject-parsed",
            key=f"bandstructures/{validate_ids([task_id])[0]}.json.gz",
            decoder=lambda x: load_json(x, deser=True),
        )[0][0]["data"]

    def get_bandstructure_from_material_id(
        self,
        material_id: str,
        path_type: BSPathType = BSPathType.setyawan_curtarolo,
        line_mode=True,
    ):
        """Get the band structure pymatgen object associated with a Materials Project ID.

        Arguments:
            material_id (str): Materials Project ID for a material
            path_type (BSPathType): k-point path selection convention
            line_mode (bool): Whether to return data for a line-mode calculation

        Returns:
            bandstructure (Union[BandStructure, BandStructureSymmLine]): BandStructure or BandStructureSymmLine object
        """
        if line_mode:
            bs_doc = self.es_rester.search(
                material_ids=material_id, fields=["bandstructure"]
            )
            if not bs_doc:
                raise MPRestError("No electronic structure data found.")

            if (bs_data := bs_doc[0]["bandstructure"]) is None:
                raise MPRestError(
                    f"No {path_type.value} band structure data found for {material_id}"
                )

            bs_data: dict = (
                bs_data.model_dump() if self.use_document_model else bs_data  # type: ignore
            )

            if bs_data.get(path_type.value, None) is None:
                raise MPRestError(
                    f"No {path_type.value} band structure data found for {material_id}"
                )
            bs_task_id = bs_data[path_type.value]["task_id"]

        else:
            if not (
                bs_doc := self.es_rester.search(
                    material_ids=material_id, fields=["dos"]
                )
            ):
                raise MPRestError("No electronic structure data found.")

            if (bs_data := bs_doc[0]["dos"]) is None:
                raise MPRestError(
                    f"No uniform band structure data found for {material_id}"
                )

            bs_data: dict = (
                bs_data.model_dump() if self.use_document_model else bs_data  # type: ignore
            )

            if bs_data.get("total", None) is None:
                raise MPRestError(
                    f"No uniform band structure data found for {material_id}"
                )
            bs_task_id = bs_data["total"]["1"]["task_id"]

        bs_obj = self.get_bandstructure_from_task_id(bs_task_id)

        if bs_obj:
            return bs_obj
        raise MPRestError("No band structure object found.")


class DosRester(BaseESPropertyRester):
    suffix = "materials/electronic_structure/dos"

    def search_dos_summary(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "MPRester.electronic_structure_dos.search_dos_summary is deprecated. "
            "Please use MPRester.electronic_structure_dos.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        band_gap: tuple[float, float] | None = None,
        efermi: tuple[float, float] | None = None,
        element: Element | str | None = None,
        magnetic_ordering: Ordering | str | None = None,
        orbital: OrbitalType | str | None = None,
        projection_type: DOSProjectionType | str = DOSProjectionType.total,
        spin: Spin | str = Spin.up,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query density of states summary data in electronic structure docs using a variety of search criteria.

        Arguments:
            band_gap (Tuple[float,float]): Minimum and maximum band gap in eV to consider.
            efermi (Tuple[float,float]): Minimum and maximum fermi energy in eV to consider.
            element (Element or str): Element for element-projected dos data.
            magnetic_ordering (Ordering or str): Magnetic ordering of the material.
            orbital (OrbitalType or str): Orbital for orbital-projected dos data.
            projection_type (DOSProjectionType or str): Projection type of dos data. Default is the total dos.
            spin (Spin or str): Spin channel of dos data. If non spin-polarized data is stored in Spin.up
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in ElectronicStructureDoc to return data for.
                Default is material_id and last_updated if all_fields is False.

        Returns:
            ([ElectronicStructureDoc]) List of electronic structure documents
        """
        query_params: dict = defaultdict(dict)

        query_params["projection_type"] = (
            DOSProjectionType[projection_type]
            if isinstance(projection_type, str)
            else projection_type
        ).value
        query_params["spin"] = (Spin[spin] if isinstance(spin, str) else spin).value

        if (
            query_params["projection_type"] == DOSProjectionType.elemental.value
            and element is None
        ):
            raise MPRestError(
                "To query element-projected DOS, you must also specify the `element` onto which the DOS is projected."
            )

        if (
            query_params["projection_type"] == DOSProjectionType.orbital.value
            and orbital is None
        ):
            raise MPRestError(
                "To query orbital-projected DOS, you must also specify the `orbital` character onto which the DOS is projected."
            )

        if element:
            query_params["element"] = (
                Element[element] if isinstance(element, str) else element
            ).value

        if orbital:
            query_params["orbital"] = (
                OrbitalType[orbital] if isinstance(orbital, str) else orbital
            ).value

        if band_gap:
            query_params.update(
                {"band_gap_min": band_gap[0], "band_gap_max": band_gap[1]}
            )

        if efermi:
            query_params.update({"efermi_min": efermi[0], "efermi_max": efermi[1]})

        if magnetic_ordering:
            query_params.update(
                {
                    "magnetic_ordering": (
                        Ordering[magnetic_ordering]
                        if isinstance(magnetic_ordering, str)
                        else magnetic_ordering
                    ).value
                }
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

    def get_dos_from_task_id(self, task_id: str) -> CompleteDos:
        """Get the density of states pymatgen object associated with a given calculation ID.

        Arguments:
            task_id (str): Task ID for the density of states calculation

        Returns:
            bandstructure (CompleteDos): CompleteDos object
        """
        return self._query_open_data(
            bucket="materialsproject-parsed",
            key=f"dos/{validate_ids([task_id])[0]}.json.gz",
            decoder=lambda x: load_json(x, deser=True),
        )[0][0]["data"]

    def get_dos_from_material_id(self, material_id: str):
        """Get the complete density of states pymatgen object associated with a Materials Project ID.

        Arguments:
            material_id (str): Materials Project ID for a material

        Returns:
            dos (CompleteDos): CompleteDos object
        """
        if not (
            dos_doc := self.es_rester.search(material_ids=material_id, fields=["dos"])
        ):
            return None

        if not (dos_data := dos_doc[0].get("dos")):
            raise MPRestError(f"No density of states data found for {material_id}")

        dos_task_id = (dos_data.model_dump() if self.use_document_model else dos_data)[
            "total"
        ]["1"]["task_id"]
        if dos_obj := self.get_dos_from_task_id(dos_task_id):
            return dos_obj

        raise MPRestError("No density of states object found.")
