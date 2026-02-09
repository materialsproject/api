from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pyarrow as pa
from deltalake import DeltaTable, QueryBuilder
from emmet.core.mpid import MPID, AlphaID
from emmet.core.tasks import CoreTaskDoc
from emmet.core.trajectory import RelaxTrajectory

from mp_api.client.core import BaseRester, MPRestError
from mp_api.client.core.utils import validate_ids

if TYPE_CHECKING:
    from typing import Any

    from pydantic import BaseModel


class TaskRester(BaseRester):
    suffix: str = "materials/tasks"
    document_model: type[BaseModel] = CoreTaskDoc  # type: ignore
    primary_key: str = "task_id"
    delta_backed = True

    def get_trajectory(self, task_id: MPID | AlphaID | str) -> list[dict[str, Any]]:
        """Returns a Trajectory object containing the geometry of the
        material throughout a calculation. This is most useful for
        observing how a material relaxes during a geometry optimization.

        Args:
            task_id (str, MPID, AlphaID): Task ID

        Returns:
            list of dict representing emmet.core.trajectory.Trajectory
        """
        as_alpha = str(AlphaID(task_id, padlen=8)).split("-")[-1]
        traj_tbl = DeltaTable(
            "s3a://materialsproject-parsed/core/trajectories/",
            storage_options={"AWS_SKIP_SIGNATURE": "true", "AWS_REGION": "us-east-1"},
        )

        traj_data = pa.table(
            QueryBuilder()
            .register("traj", traj_tbl)
            .execute(
                f"""
                SELECT *
                FROM   traj
                WHERE  identifier='{as_alpha}'
                """
            )
            .read_all()
        ).to_pylist(maps_as_pydicts="strict")

        if not traj_data:
            raise MPRestError(f"No trajectory data for {task_id} found")

        return RelaxTrajectory(**traj_data[0]).to_pmg().as_dict()

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
    ) -> list[CoreTaskDoc] | list[dict]:
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
            fields (List[str]): List of fields in CoreTaskDoc to return data for.
                Default is material_id, last_updated, and formula_pretty if all_fields is False.

        Returns:
            ([CoreTaskDoc], [dict]) List of task documents or dictionaries.
        """
        query_params: dict = {}

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

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params,
        )
