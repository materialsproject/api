from __future__ import annotations

import warnings
from datetime import datetime

from emmet.core.tasks import TaskDoc

from mp_api.client.core import BaseRester, MPRestError
from mp_api.client.core.utils import validate_ids


class TaskRester(BaseRester[TaskDoc]):
    suffix = "materials/tasks"
    document_model = TaskDoc  # type: ignore
    primary_key = "task_id"

    def get_trajectory(self, task_id):
        """Returns a Trajectory object containing the geometry of the
        material throughout a calculation. This is most useful for
        observing how a material relaxes during a geometry optimization.

        Args:
            task_id (str): Task ID

        """
        traj_data = self._query_resource_data(
            {"task_ids": [task_id]}, suburl="trajectory/", use_document_model=False
        )[0].get(
            "trajectories", None
        )  # type: ignore

        if traj_data is None:
            raise MPRestError(f"No trajectory data for {task_id} found")

        return traj_data

    def search(
        self,
        task_ids: str | list[str] | None = None,
        elements: list[str] | None = None,
        exclude_elements: list[str] | None = None,
        formula: str | list[str] | None = None,
        calc_type: str | None = None,
        run_type: str | None = None,
        task_type: str | None = None,
        chemsys: str | list[str] | None = None,
        last_updated: tuple[datetime, datetime] | None = None,
        batches: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = False,
        fields: list[str] | None = None,
        facets: str | list[str] | None = None,
    ) -> list[TaskDoc] | list[dict]:
        """Query core task docs using a variety of search criteria.

        Arguments:
            task_ids (str, List[str]): List of Materials Project IDs to return data for.
            chemsys: (str, List[str]): A list of chemical systems to search for.
            elements: (List[str]): A list of elements to search for.
            exclude_elements (List[str]): A list of elements to exclude.
            formula (str, List[str]): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*). A list of chemical formulas can also be passed
                (e.g., [Fe2O3, ABO3]).
            last_updated (tuple[datetime, datetime]): A tuple of min and max UTC formatted datetimes.
            batches (str, List[str]): A list of batch IDs to search for.
            run_type (str): The type of task to search for. Can be one of the following:
                #TODO: check enum
            task_type (str): The type of task to search for. Can be one of the following:
                #TODO check enum
            calc_type (str): The type of calculation to search for. A combination of the run_type and task_type.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk. Max size is 100.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in TaskDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.
            facets (str, List[str]): List of facets to return data for.

        Returns:
            ([TaskDoc], [dict]) List of task documents or dictionaries.
        """
        query_params = {}  # type: dict

        if task_ids:
            if isinstance(task_ids, str):
                task_ids = [task_ids]

            query_params.update({"task_ids": ",".join(validate_ids(task_ids))})

        if formula:
            query_params.update(
                {"formula": ",".join(formula) if isinstance(formula, list) else formula}
            )

        if chemsys:
            query_params.update(
                {"chemsys": ",".join(chemsys) if isinstance(chemsys, list) else chemsys}
            )

        if elements:
            query_params.update({"elements": ",".join(elements)})

        if exclude_elements:
            query_params.update({"exclude_elements": ",".join(exclude_elements)})

        if last_updated:
            query_params.update(
                {
                    "last_updated_min": last_updated[0],
                    "last_updated_max": last_updated[1],
                }
            )

        if task_type:
            query_params.update({"task_type": task_type})

        if calc_type:
            query_params.update({"calc_type": calc_type})

        if run_type:
            query_params.update({"run_type": run_type})

        if batches:
            query_params.update(
                {"batches": ".".join(batches) if isinstance(batches, list) else batches}
            )

        if facets:
            query_params.update(
                {"facets": ",".join(facets) if isinstance(facets, list) else facets}
            )

        if all_fields:
            warnings.warn(
                """Please only use all_fields=True when necessary, as it may cause slow query.
                """
            )
        if fields and ("calcs_reversed" in fields or "orig_inputs" in fields):
            warnings.warn(
                """Please only include calcs_reversed and orig_inputs when necessary, as it may cause slow query.
                """
            )

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
