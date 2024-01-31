from __future__ import annotations

from collections import defaultdict

from emmet.core.elasticity import ElasticityDoc

from mp_api.client.core import BaseRester
from mp_api.client.core.utils import validate_ids


class ElasticityRester(BaseRester[ElasticityDoc]):
    suffix = "materials/elasticity"
    document_model = ElasticityDoc  # type: ignore
    primary_key = "material_id"

    def search(
        self,
        material_ids: str | list[str] | None = None,
        elastic_anisotropy: tuple[float, float] | None = None,
        g_voigt: tuple[float, float] | None = None,
        g_reuss: tuple[float, float] | None = None,
        g_vrh: tuple[float, float] | None = None,
        k_voigt: tuple[float, float] | None = None,
        k_reuss: tuple[float, float] | None = None,
        k_vrh: tuple[float, float] | None = None,
        poisson_ratio: tuple[float, float] | None = None,
        num_chunks: int | None = None,
        chunk_size: int = 1000,
        all_fields: bool = True,
        fields: list[str] | None = None,
    ) -> list[ElasticityDoc] | list[dict]:
        """Query elasticity docs using a variety of search criteria.

        Arguments:
            material_ids (str, List[str]): A single Material ID string or list of strings
                (e.g., mp-149, [mp-149, mp-13]).
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
            num_chunks (int): Maximum number of chunks of data to yield. None will yield all possible.
            chunk_size (int): Number of data entries per chunk.
            all_fields (bool): Whether to return all fields in the document. Defaults to True.
            fields (List[str]): List of fields in ElasticityDoc to return data for.
                Default is material_id and prett-formula if all_fields is False.

        Returns:
            ([ElasticityDoc], [dict]) List of elasticity documents or dictionaries.
        """
        query_params = defaultdict(dict)  # type: dict

        if material_ids:
            if isinstance(material_ids, str):
                material_ids = [material_ids]

            query_params.update({"material_ids": ",".join(validate_ids(material_ids))})

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
