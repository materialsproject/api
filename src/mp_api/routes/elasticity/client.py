from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester
from mp_api.routes.elasticity.models import ElasticityDoc

import warnings


class ElasticityRester(BaseRester[ElasticityDoc]):

    suffix = "elasticity"
    document_model = ElasticityDoc  # type: ignore
    primary_key = "task_id"

    def search_elasticity_docs(
        self,
        k_voigt: Optional[Tuple[float, float]] = None,
        k_reuss: Optional[Tuple[float, float]] = None,
        k_vrh: Optional[Tuple[float, float]] = None,
        g_voigt: Optional[Tuple[float, float]] = None,
        g_reuss: Optional[Tuple[float, float]] = None,
        g_vrh: Optional[Tuple[float, float]] = None,
        elastic_anisotropy: Optional[Tuple[float, float]] = None,
        poisson_ratio: Optional[Tuple[float, float]] = None,
        sort_field: Optional[str] = None,
        ascending: Optional[bool] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: Optional[List[str]] = None,
    ):
        """
        Query elasticity docs using a variety of search criteria.

        Arguments:
            k_voigt (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt average of the bulk modulus.
            k_reuss (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Reuss average of the bulk modulus.
            k_vrh (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt-Reuss-Hill average of the bulk modulus.
            g_voigt (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt average of the shear modulus.
            g_reuss (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Reuss average of the shear modulus.
            g_vrh (Tuple[float,float]): Minimum and maximum value in GPa to consider for
                the Voigt-Reuss-Hill average of the shear modulus.
            elastic_anisotropy (Tuple[float,float]): Minimum and maximum value to consider for
                the elastic anisotropy.
            poisson_ratio (Tuple[float,float]): Minimum and maximum value to consider for
                Poisson's ratio.
            sort_field (str): Field used to sort results.
            ascending (bool): Whether sorting should be in ascending order.
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

        if sort_field:
            query_params.update({"sort_field": sort_field})

        if ascending is not None:
            query_params.update({"ascending": ascending})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        return super().search(
            num_chunks=num_chunks,
            chunk_size=chunk_size,
            all_fields=all_fields,
            fields=fields,
            **query_params
        )
