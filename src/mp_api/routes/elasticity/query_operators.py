from typing import Optional
from fastapi import Query
from maggma.api.query_operator import QueryOperator
from maggma.api.utils import STORE_PARAMS

from collections import defaultdict


class BulkModulusQuery(QueryOperator):
    """
    Method to generate a query for ranges of bulk modulus values
    """

    def query(
        self,
        k_voigt_max: Optional[float] = Query(
            None,
            description="Maximum value for the Voigt average of the bulk modulus in GPa.",
        ),
        k_voigt_min: Optional[float] = Query(
            None,
            description="Minimum value for the Voigt average of the bulk modulus in GPa.",
        ),
        k_reuss_max: Optional[float] = Query(
            None,
            description="Maximum value for the Reuss average of the bulk modulus in GPa.",
        ),
        k_reuss_min: Optional[float] = Query(
            None,
            description="Minimum value for the Reuss average of the bulk modulus in GPa.",
        ),
        k_vrh_max: Optional[float] = Query(
            None,
            description="Maximum value for the Voigt-Reuss-Hill average of the bulk modulus in GPa.",
        ),
        k_vrh_min: Optional[float] = Query(
            None,
            description="Minimum value for the Voigt-Reuss-Hill average of the bulk modulus in GPa.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "elasticity.k_voigt": [k_voigt_min, k_voigt_max],
            "elasticity.k_reuss": [k_reuss_min, k_reuss_max],
            "elasticity.k_vrh": [k_vrh_min, k_vrh_max],
        }

        for entry in d:
            if d[entry][0] is not None:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1] is not None:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}


class ShearModulusQuery(QueryOperator):
    """
    Method to generate a query for ranges of shear modulus values
    """

    def query(
        self,
        g_voigt_max: Optional[float] = Query(
            None,
            description="Maximum value for the Voigt average of the shear modulus in GPa.",
        ),
        g_voigt_min: Optional[float] = Query(
            None,
            description="Minimum value for the Voigt average of the shear modulus in GPa.",
        ),
        g_reuss_max: Optional[float] = Query(
            None,
            description="Maximum value for the Reuss average of the shear modulus in GPa.",
        ),
        g_reuss_min: Optional[float] = Query(
            None,
            description="Minimum value for the Reuss average of the shear modulus in GPa.",
        ),
        g_vrh_max: Optional[float] = Query(
            None,
            description="Maximum value for the Voigt-Reuss-Hill average of the shear modulus in GPa.",
        ),
        g_vrh_min: Optional[float] = Query(
            None,
            description="Minimum value for the Voigt-Reuss-Hill average of the shear modulus in GPa.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "elasticity.g_voigt": [g_voigt_min, g_voigt_max],
            "elasticity.g_reuss": [g_reuss_min, g_reuss_max],
            "elasticity.g_vrh": [g_vrh_min, g_vrh_max],
        }

        for entry in d:
            if d[entry][0] is not None:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1] is not None:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}


class PoissonQuery(QueryOperator):
    """
    Method to generate a query for ranges of
    elastic anisotropy and poisson ratio values
    """

    def query(
        self,
        elastic_anisotropy_max: Optional[float] = Query(
            None, description="Maximum value for the elastic anisotropy.",
        ),
        elastic_anisotropy_min: Optional[float] = Query(
            None, description="Maximum value for the elastic anisotropy.",
        ),
        poisson_max: Optional[float] = Query(
            None, description="Maximum value for Poisson's ratio.",
        ),
        poisson_min: Optional[float] = Query(
            None, description="Minimum value for Poisson's ratio.",
        ),
    ) -> STORE_PARAMS:

        crit = defaultdict(dict)  # type: dict

        d = {
            "elasticity.universal_anisotropy": [
                elastic_anisotropy_min,
                elastic_anisotropy_max,
            ],
            "elasticity.homogeneous_poisson": [poisson_min, poisson_max],
        }

        for entry in d:
            if d[entry][0] is not None:
                crit[entry]["$gte"] = d[entry][0]

            if d[entry][1] is not None:
                crit[entry]["$lte"] = d[entry][1]

        return {"criteria": crit}


class ChemsysQuery(QueryOperator):
    """
    Method to generate a query on chemsys data
    """

    def query(
        self,
        chemsys: Optional[str] = Query(
            None, description="Dash-delimited list of elements in the material.",
        ),
    ):

        crit = {}  # type: dict

        if chemsys:
            eles = chemsys.split("-")
            chemsys = "-".join(sorted(eles))

            crit["chemsys"] = chemsys

        return {"criteria": crit}
