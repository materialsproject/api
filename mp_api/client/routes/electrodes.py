from __future__ import annotations

import warnings
from collections import defaultdict

from emmet.core.electrode import InsertionElectrodeDoc
from pymatgen.core.periodic_table import Element

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class ElectrodeRester(BaseRester[InsertionElectrodeDoc]):
    suffix = "materials/insertion_electrodes"
    document_model = InsertionElectrodeDoc  # type: ignore
    primary_key = "battery_id"

    def search_electrode_docs(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "MPRester.electrode.search_electrode_docs is deprecated. Please use MPRester.electrode.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(  # pragma: ignore
        self,
        material_ids: str | list[str] | None = None,
        battery_ids: str | list[str] | None = None,
        average_voltage: tuple[float, float] | None = None,
        capacity_grav: tuple[float, float] | None = None,
        capacity_vol: tuple[float, float] | None = None,
        elements: list[str] | None = None,
        energy_grav: tuple[float, float] | None = None,
        energy_vol: tuple[float, float] | None = None,
        exclude_elements: list[str] | None = None,
        formula: str | list[str] | None = None,
        fracA_charge: tuple[float, float] | None = None,
        fracA_discharge: tuple[float, float] | None = None,
        max_delta_volume: tuple[float, float] | None = None,
        max_voltage_step: tuple[float, float] | None = None,
        num_elements: tuple[int, int] | None = None,
        num_steps: tuple[int, int] | None = None,
        stability_charge: tuple[float, float] | None = None,
        stability_discharge: tuple[float, float] | None = None,
        working_ion: Element | None = None,
        sort_fields: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query equations of state docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
            battery_ids (str, List[str]): A single battery ID string or list of strings
                (e.g., mp-22526_Li, [mp-22526_Li, mp-22526_Ca]).
            average_voltage (Tuple[float,float]): Minimum and maximum value of the average voltage for a particular
                voltage step in V.
            capacity_grav (Tuple[float,float]): Minimum and maximum value of the gravimetric capacity in maH/g.
            capacity_vol (Tuple[float,float]): Minimum and maximum value of the volumetric capacity in maH/cc.
            elements (List[str]): A list of elements for the framework material.
            energy_grav (Tuple[float,float]): Minimum and maximum value of the gravimetric energy (specific energy)
                in Wh/kg.
            energy_vol (Tuple[float,float]): Minimum and maximum value of the volumetric energy (energy density)
                in Wh/l.
            exclude_elements (List[str]): A list of elements to exclude for the framework material.
            formula (str, List[str]): Chemical formula or list of chemical formulas of any of the materials
                associated with the electrode system. This includes materials partially along the charge-discharge path.
            fracA_charge (Tuple[float,float]): Minimum and maximum value of the atomic fraction of the working ion
                in the charged state.
            fracA_discharge (Tuple[float,float]): Minimum and maximum value of the atomic fraction of the working ion
                in the discharged state.
            max_delta_volume (Tuple[float,float]): Minimum and maximum value of the max volume change in percent for a
                particular voltage step.
            max_voltage_step (Tuple[float,float]): Minimum and maximum value of the maximum voltage for a particular
                voltage step in V.
            num_elements (Tuple[int,int]): Minimum and maximum number of elements to consider.
            num_steps (int): Number of distinct voltage steps from charged to discharged based on stable intermediates.
            stability_charge (Tuple[float,float]): Minimum and maximum value of the energy above hull of the charged
                material.
            stability_discharge (Tuple[float,float]): Minimum and maximum value of the energy above hull of the
                discharged material.
            working_ion (Element, List[Element]): Element or list of elements of the working ion.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in InsertionElectrodeDoc to return data for.
                Default is battery_id and last_updated if all_fields is False.

        Returns:
            ([InsertionElectrodeDoc]) List of insertion electrode documents.
        """
        query_params = defaultdict(dict)  # type: dict

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

        if battery_ids:
            if isinstance(battery_ids, str):
                battery_ids = [battery_ids]

            query_params.update({"battery_ids": ",".join(validate_ids(battery_ids))})

        if working_ion:
            if isinstance(working_ion, (str, Element)):
                working_ion = [working_ion]  # type: ignore

            query_params.update({"working_ion": ",".join([str(ele) for ele in working_ion])})  # type: ignore

        if formula:
            if isinstance(formula, str):
                formula = [formula]

            query_params.update({"formula": ",".join(formula)})

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if num_elements:
            if isinstance(num_elements, int):
                num_elements = (num_elements, num_elements)
            query_params.update(
                {"nelements_min": num_elements[0], "nelements_max": num_elements[1]}
            )

        if exclude_elements:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
            )

        for param, value in locals().items():
            if (
                param
                not in [
                    "__class__",
                    "self",
                    "working_ion",
                    "query_params",
                    "num_elements",
                ]
                and value
            ):
                if isinstance(value, tuple):
                    query_params.update(
                        {f"{param}_min": value[0], f"{param}_max": value[1]}
                    )
                else:
                    query_params.update({param: value})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super()._search(**query_params)
