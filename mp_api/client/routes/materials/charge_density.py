from __future__ import annotations

from pathlib import Path
from typing import Literal

from emmet.core.charge_density import ChgcarDataDoc
from monty.serialization import dumpfn

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class ChargeDensityRester(BaseRester[ChgcarDataDoc]):
    suffix = "materials/charge_density"
    primary_key = "fs_id"
    document_model = ChgcarDataDoc  # type: ignore
    boto_resource = None

    def download_for_task_ids(
        self,
        path: str,
        task_ids: list[str],
        ext: Literal["json.gz", "json", "mpk", "mpk.gz"] = "json.gz",  # type: ignore
    ) -> int:
        """Download a set of charge densities.

        :param path: Your local directory to save the charge densities to. Each charge
        density will be serialized as a separate JSON file with name given by the relevant
        task_id.
        :param task_ids: A list of task_ids.
        :param ext: Choose from any file type supported by `monty`, e.g. json or msgpack.
        :return: An integer for the number of charge densities saved.
        """
        num_downloads = 0
        path_obj = Path(path)
        chgcar_summary_docs = self.search(task_ids=task_ids)
        for entry in chgcar_summary_docs:
            fs_id = entry.fs_id  # type: ignore
            task_id = entry.task_id  # type: ignore
            doc = self.get_data_by_id(fs_id)
            dumpfn(doc, path_obj / f"{task_id}.{ext}")
            num_downloads += 1
        return num_downloads

    def search(  # type: ignore
        self,
        task_ids: list[str] | None = None,
        num_chunks: int | None = 1,
        chunk_size: int = 10,
    ) -> list[ChgcarDataDoc] | list[dict]:  # type: ignore
        """A search method to find what charge densities are available via this API.

        Arguments:
            task_ids (List[str]): List of Materials Project IDs to return data for.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.

        Returns:
            A list of ChgcarDataDoc that contain task_id references.
        """
        query_params = {}

        if task_ids:
            query_params.update({"task_ids": ",".join(validate_ids(task_ids))})

        return super()._search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=False,
            fields=["last_updated", "task_id", "fs_id"],
            **query_params,
        )
