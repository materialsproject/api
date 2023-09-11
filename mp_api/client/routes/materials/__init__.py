from __future__ import annotations

from .absorption import AbsorptionRester
from .bonds import BondsRester
from .chemenv import ChemenvRester
from .dielectric import DielectricRester
from .doi import DOIRester
from .elasticity import ElasticityRester
from .electrodes import ElectrodeRester
from .electronic_structure import (
    BandStructureRester,
    DosRester,
    ElectronicStructureRester,
)
from .eos import EOSRester
from .fermi import FermiRester
from .grain_boundary import GrainBoundaryRester
from .magnetism import MagnetismRester
from .oxidation_states import OxidationStatesRester
from .phonon import PhononRester
from .piezo import PiezoRester
from .provenance import ProvenanceRester
from .robocrys import RobocrysRester
from .similarity import SimilarityRester
from .substrates import SubstratesRester
from .summary import SummaryRester
from .surface_properties import SurfacePropertiesRester
from .synthesis import SynthesisRester
from .tasks import TaskRester
from .thermo import ThermoRester
from .xas import XASRester

try:
    from .alloys import AlloysRester
except ImportError:
    AlloysRester = None  # type: ignore

try:
    from .charge_density import ChargeDensityRester
except ImportError:
    ChargeDensityRester = None  # type: ignore
