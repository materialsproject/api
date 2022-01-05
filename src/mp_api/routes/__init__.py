from mp_api.routes.eos import EOSRester
from mp_api.routes.materials import MaterialsRester
from mp_api.routes.similarity import SimilarityRester
from mp_api.routes.tasks import TaskRester
from mp_api.routes.xas import XASRester
from mp_api.routes.fermi import FermiRester
from mp_api.routes.grain_boundary import GrainBoundaryRester
from mp_api.routes.substrates import SubstratesRester
from mp_api.routes.surface_properties import SurfacePropertiesRester
from mp_api.routes.phonon import PhononRester
from mp_api.routes.elasticity import ElasticityRester
from mp_api.routes.thermo import ThermoRester
from mp_api.routes.dielectric import DielectricRester
from mp_api.routes.doi import DOIRester
from mp_api.routes.piezo import PiezoRester
from mp_api.routes.magnetism import MagnetismRester
from mp_api.routes.summary import SummaryRester
from mp_api.routes.robocrys import RobocrysRester
from mp_api.routes.molecules import MoleculesRester
from mp_api.routes.synthesis import SynthesisRester
from mp_api.routes.electrodes import ElectrodeRester
from mp_api.routes.charge_density import ChargeDensityRester
from mp_api.routes.electronic_structure import (
    ElectronicStructureRester,
    BandStructureRester,
    DosRester,
)
from mp_api.routes.oxidation_states import OxidationStatesRester
from mp_api.routes.provenance import ProvenanceRester
from mp_api.routes._user_settings import UserSettingsRester
from mp_api.routes._general_store import GeneralStoreRester
from mp_api.routes.bonds import BondsRester
