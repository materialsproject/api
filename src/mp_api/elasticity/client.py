from typing import List, Optional, Tuple
from collections import defaultdict

from mp_api.core.client import BaseRester, MPRestError
from mp_api.elasticity.models import ElasticityDoc

import warnings


class ElasticityRester(BaseRester):

    suffix = "elasticity"
    document_model = ElasticityDoc  # type: ignore

    def get_elasticity_from_material_id(self, material_id: str):
        """
        Get elasticity data for a given Materials Project ID.

        Arguments:
            material_id (str): Materials project ID

        Returns:
            results (Dict): Dictionary containing elasticity data.
        """

        result = self._make_request("{}/?all_fields=true".format(material_id))

        if len(result.get("data", [])) > 0:
            return result
        else:
            raise MPRestError("No document found")

    def search_elasticity_docs(
        self,
        chemsys: Optional[str] = None,
        k_voigt: Optional[Tuple[float, float]] = None,
        k_reuss: Optional[Tuple[float, float]] = None,
        k_vrh: Optional[Tuple[float, float]] = None,
        g_voigt: Optional[Tuple[float, float]] = None,
        g_reuss: Optional[Tuple[float, float]] = None,
        g_vrh: Optional[Tuple[float, float]] = None,
        elastic_anisotropy: Optional[Tuple[float, float]] = None,
        poisson_ratio: Optional[Tuple[float, float]] = None,
        num_chunks: Optional[int] = None,
        chunk_size: int = 100,
        fields: Optional[List[str]] = None,
    ):
        """
        Query equations of state docs using a variety of search criteria.

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
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            fields (List[str]): List of fields in EOSDoc to return data for.
                Default is material_id only.

        Yields:
            ([dict]) List of dictionaries containing data for entries defined in 'fields'.
                Defaults to Materials Project IDs only.
        """

        query_params = defaultdict(dict)  # type: dict

        if chunk_size <= 0 or chunk_size > 100:
            warnings.warn("Improper chunk size given. Setting value to 100.")
            chunk_size = 100

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

        if fields:
            query_params.update({"fields": ",".join(fields)})

        query_params = {
            entry: query_params[entry]
            for entry in query_params
            if query_params[entry] is not None
        }

        query_params.update({"limit": chunk_size, "skip": 0})
        count = 0
        while True:
            query_params["skip"] = count * chunk_size
            results = self.query(query_params).get("data", [])

            if not any(results) or (num_chunks is not None and count == num_chunks):
                break

            count += 1
            yield results
