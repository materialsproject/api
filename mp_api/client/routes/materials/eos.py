from __future__ import annotations

import warnings
from collections import defaultdict

from emmet.core.eos import EOSDoc

from mp_api.client.core import BaseRester, MPRestError, MPRestWarning
from mp_api.client.core.utils import validate_ids


class EOSRester(BaseRester):
    suffix = "materials/eos"
    document_model = EOSDoc  # type: ignore
    primary_key = "task_id"

    def search(
        self,
        task_ids: str | list[str] | None = None,
        energies: tuple[float, float] | None = None,
        volumes: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
        **kwargs,
    ) -> list[EOSDoc] | list[dict]:
        """Query equations of state docs using a variety of search criteria.

        Arguments:
            task_ids (str, List[str]): Search for equation of states associated with the specified task IDs
            energies (Tuple[float,float]): Minimum and maximum energy in eV/atom to consider for EOS plot range.
            volumes (Tuple[float,float]): Minimum and maximum volume in A³/atom to consider for EOS plot range.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in EOSDoc to return data for.
                Default is material_id only if all_fields is False.
            **kwargs : used for handling deprecated kwargs

        Returns:
            ([EOSDoc], [dict]) List of equations of state docs or dictionaries.
        """
        query_params: dict = defaultdict(dict)

        if "material_ids" in kwargs:
            if task_ids:
                raise MPRestError(
                    "You have specified both `task_ids` and the deprecated `material_ids` tag. "
                    "Please specify only `task_ids`."
                )
            task_ids = kwargs.pop("material_ids")
            warnings.warn(
                "`material_id` has been replaced by `task_id` in the EOS endpoint. "
                "Please migrate to using the newer field name.",
                stacklevel=2,
                category=MPRestWarning,
            )

        if task_ids:
            query_params["task_ids"] = ",".join(
                validate_ids([task_ids] if isinstance(task_ids, str) else task_ids)
            )

        if volumes:
            query_params.update({"volumes_min": volumes[0], "volumes_max": volumes[1]})

        if energies:
            query_params.update(
                {"energies_min": energies[0], "energies_max": energies[1]}
            )

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
