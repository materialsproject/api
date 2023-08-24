from __future__ import annotations

import warnings
from collections import defaultdict

from emmet.core.elasticity_legacy import ElasticityDoc

from mp_api.client.core import BaseRester


class ElasticityRester(BaseRester[ElasticityDoc]):
    suffix = "materials/elasticity"
    document_model = ElasticityDoc  # type: ignore
    primary_key = "task_id"

    def search_elasticity_docs(self, *args, **kwargs):  # pragma: no cover
        """Deprecated."""
        warnings.warn(
            "MPRester.elasticity.search_elasticity_docs is deprecated. Please use MPRester.elasticity.search instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.search(*args, **kwargs)

    def search(
        self,
        elastic_anisotropy: tuple[float, float] | None = None,
        g_voigt: tuple[float, float] | None = None,
        g_reuss: tuple[float, float] | None = None,
        g_vrh: tuple[float, float] | None = None,
        k_voigt: tuple[float, float] | None = None,
        k_reuss: tuple[float, float] | None = None,
        k_vrh: tuple[float, float] | None = None,
        poisson_ratio: tuple[float, float] | None = None,
        sort_fields: list[str] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ):
        """Query elasticity docs using a variety of search criteria.

        Arguments:
            elastic_anisotropy (Tuple[float,float]): Minimum and maximum value to consider for
                the elastic anisotropy.
            g_voigt (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt average of the shear modulus.
            g_reuss (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Reuss average of the shear modulus.
            g_vrh (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt-Reuss-Hill average of the shear modulus.
            k_voigt (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt average of the bulk modulus.
            k_reuss (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Reuss average of the bulk modulus.
            k_vrh (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt-Reuss-Hill average of the bulk modulus.
            poisson_ratio (Tuple[float,float]): Minimum and maximum value to consider for
                Poisson's ratio.
            sort_fields (List[str]): Fields used to sort results. Prefix with '-' to sort in descending order.
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in ElasticityDoc to return data for.
                Default is material_id and prett-formula if all_fields is False.

        Returns:
            ([ElasticityDoc]) List of elasticity documents.
        """
        query_params = defaultdict(dict)  # type: dict

        if k_voigt:
            query_params.update({"k_voigt_min": k_voigt[0], "k_voigt_max": k_voigt[1]})

        if k_reuss:
            query_params.update({"k_reuss_min": k_reuss[0], "k_reuss_max": k_reuss[1]})

        if k_vrh:
            query_params.update({"k_vrh_min": k_vrh[0], "g_vrh_max": k_vrh[1]})

        if g_voigt:
            query_params.update({"g_voigt_min": g_voigt[0], "g_voigt_max": g_voigt[1]})

        if g_reuss:
            query_params.update({"g_reuss_min": g_reuss[0], "g_reuss_max": g_reuss[1]})

        if g_vrh:
            query_params.update({"g_vrh_min": g_vrh[0], "g_vrh_max": g_vrh[1]})

        if elastic_anisotropy:
            query_params.update(
                {
                    "elastic_anisotropy_min": elastic_anisotropy[0],
                    "elastic_anisotropy_max": elastic_anisotropy[1],
                }
            )

        if poisson_ratio:
            query_params.update(
                {"poisson_min": poisson_ratio[0], "poisson_max": poisson_ratio[1]}
            )

        if sort_fields:
            query_params.update(
                {"_sort_fields": ",".join([s.strip() for s in sort_fields])}
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
