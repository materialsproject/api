from typing import List
from pydantic import BaseModel, Field


class ElasticityData(BaseModel):
    """
    Elastic tensors and associated information.
    """

    k_voigt: float = Field(
        None,
        description="Voigt average of the bulk modulus.",
    )

    k_reuss: float = Field(
        None,
        description="Reuss average of the bulk modulus in GPa.",
    )

    k_vrh: float = Field(
        None,
        description="Voigt-Reuss-Hill average of the bulk modulus in GPa.",
    )

    g_voigt: float = Field(
        None,
        description="Voigt average of the shear modulus in GPa.",
    )

    g_reuss: float = Field(
        None,
        description="Reuss average of the shear modulus in GPa.",
    )

    g_vrh: float = Field(
        None,
        description="Voigt-Reuss-Hill average of the shear modulus in GPa.",
    )

    universal_anisotropy: float = Field(
        None,
        description="Elastic anisotropy.",
    )

    homogeneous_poisson: float = Field(
        None,
        description="Poisson's ratio.",
    )

    elastic_tensor: List[List[float]] = Field(
        None,
        description="Stiffness tensor in GPa.",
    )

    compliance_tensor: List[List[float]] = Field(
        None,
        description="Compliance tensor in 10^(-12)/Pa.",
    )


class ElasticityDoc(BaseModel):
    """
    Model for a document containing elasticity data
    """

    pretty_formula: str = Field(
        None,
        description="Cleaned representation of the material formula",
    )

    chemsys: str = Field(
        None,
        description="Dash-delimited string of elements in the material",
    )

    elasticity: ElasticityData = Field(
        None,
        description="Elasticity data for the material",
    )

    task_id: str = Field(
        None,
        description="The Materials Project ID of the material. This comes in the form: mp-******",
    )
