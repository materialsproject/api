from __future__ import annotations

import json
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
        )[0].get("trajectories", None)  # type: ignore

        if traj_data is None:
            raise MPRestError(f"No trajectory data for {task_id} found")

        return traj_data

    def search(
        self,
        task_ids: str | list[str] | None = None,
        elements: list[str] | None = None,
        exclude_elements: list[str] | None = None,
        formula: str | list[str] | None = None,
        last_updated: tuple[datetime, datetime] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[TaskDoc] | list[dict]:
        """Query core task docs using a variety of search criteria.

        Arguments:
            task_ids (str, List[str]): List of Materials Project IDs to return data for.
            elements (List[str]): A list of elements.
            exclude_elements (List[str]): A list of elements to exclude.
            formula (str, List[str]): A formula including anonymized formula
                or wild cards (e.g., Fe2O3, ABO3, Si*). A list of chemical formulas can also be passed
                (e.g., [Fe2O3, ABO3]).
            last_updated (tuple[datetime, datetime]): A tuple of min and max UTC formatted datetimes.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk. Max size is 100.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in TaskDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([TaskDoc], [dict]) List of task documents or dictionaries.
        """
        query_params = {}  # type: dict

        if task_ids:
            if isinstance(task_ids, str):
                task_ids = [task_ids]

            query_params.update({"task_ids": ",".join(validate_ids(task_ids))})

        if formula:
            query_params.update({"formula": formula})

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

        if task_ids and len(query_params.keys()) == 1:
            open_data_keys = self._generate_open_data_keys(task_ids)
            query_params.update({"open_data_keys": open_data_keys})

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )

    def _generate_open_data_keys(
        self,
        task_ids: list[str],
    ) -> list[str]:
        # Construct the S3 Select query
        task_ids_string = ",".join(f"'{task_id}'" for task_id in task_ids)
        query = f"""
        SELECT s.task_id, s.nelements, s.output.spacegroup.number as spg_number, s.last_updated
        FROM S3Object s
        WHERE s.task_id IN ({task_ids_string})
        """

        # Execute the S3 Select query
        response = self.s3_client.select_object_content(
            Bucket="materialsproject-parsed",
            Key="tasks/manifest.jsonl",
            ExpressionType="SQL",
            Expression=query,
            InputSerialization={"JSON": {"Type": "LINES"}},
            OutputSerialization={"JSON": {}},
        )

        # Process the response
        results = []
        for event in response["Payload"]:
            if "Records" in event:
                records = event["Records"]["Payload"].decode("utf-8")
                results.extend(json.loads(line) for line in records.strip().split("\n"))

        # Generate open data keys
        open_data_keys = []
        for doc in results:
            nelements = doc.get("nelements")
            spg_number = doc.get("spg_number")
            dt = doc.get("last_updated")

            if None not in [nelements, spg_number, dt]:
                open_data_keys.append(
                    f"nelements={nelements}/output_spacegroup_number={spg_number}/dt={dt}"
                )

        return open_data_keys
