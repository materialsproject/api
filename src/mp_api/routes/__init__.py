from mp_api.routes.eos.client import EOSRester
from mp_api.routes.materials.client import MaterialsRester
from mp_api.routes.similarity.client import SimilarityRester
from mp_api.routes.tasks.client import TaskRester
from mp_api.routes.xas.client import XASRester
from mp_api.routes.fermi.client import FermiRester
from mp_api.routes.grain_boundary.client import GrainBoundaryRester
from mp_api.routes.substrates.client import SubstratesRester
from mp_api.routes.surface_properties.client import SurfacePropertiesRester
from mp_api.routes.phonon.client import PhononRester
from mp_api.routes.elasticity.client import ElasticityRester
from mp_api.routes.thermo.client import ThermoRester
from mp_api.routes.dielectric.client import DielectricRester
from mp_api.routes.dois.client import DOIRester
from mp_api.routes.piezo.client import PiezoRester
from mp_api.routes.magnetism.client import MagnetismRester
from mp_api.routes.summary.client import SummaryRester
from mp_api.routes.robocrys.client import RobocrysRester
from mp_api.routes.molecules.client import MoleculesRester
from mp_api.routes.synthesis.client import SynthesisRester
from mp_api.routes.electrodes.client import ElectrodeRester
from mp_api.routes.charge_density.client import ChargeDensityRester
from mp_api.routes.electronic_structure.client import (
    ElectronicStructureRester,
    BandStructureRester,
    DosRester,
)
from mp_api.routes.oxidation_states.client import OxidationStatesRester
from mp_api.routes.provenance.client import ProvenanceRester
from mp_api.routes._consumer.client import UserSettingsRester
