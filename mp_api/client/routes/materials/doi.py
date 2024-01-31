from __future__ import annotations

from collections import defaultdict

from emmet.core.dois import DOIDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class DOIRester(BaseRester[DOIDoc]):
    suffix = "doi"
    document_model = DOIDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: str | list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        query_params = defaultdict(dict)  # type: dict
        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

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
