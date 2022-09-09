from ast import Import
from .eos import EOSRester
from .materials import MaterialsRester
from .similarity import SimilarityRester
from .tasks import TaskRester
from .xas import XASRester
from .fermi import FermiRester
from .grain_boundary import GrainBoundaryRester
from .substrates import SubstratesRester
from .surface_properties import SurfacePropertiesRester
from .phonon import PhononRester
from .elasticity import ElasticityRester
from .thermo import ThermoRester
from .dielectric import DielectricRester
from .doi import DOIRester
from .piezo import PiezoRester
from .magnetism import MagnetismRester
from .summary import SummaryRester
from .molecules import MoleculesRester
from .synthesis import SynthesisRester
from .electrodes import ElectrodeRester
from .electronic_structure import (
    ElectronicStructureRester,
    BandStructureRester,
    DosRester,
)
from .oxidation_states import OxidationStatesRester
from .provenance import ProvenanceRester
from ._user_settings import UserSettingsRester
from ._general_store import GeneralStoreRester
from .bonds import BondsRester
from .robocrys import RobocrysRester

try:
    from .alloys import AlloysRester
except ImportError:
    AlloysRester = None  # type: ignore

try:
    from .charge_density import ChargeDensityRester
except ImportError:
    ChargeDensityRester = None  # type: ignore
