"""Define routes and imports to non-core materials resters."""
from __future__ import annotations

from mp_api.client.core.utils import LazyImport

MATERIALS_RESTERS: dict[str, LazyImport] = {
    route: LazyImport(f"mp_api.client.routes.materials.{module_name}.{cls_name}")
    for route, module_name, cls_name in (
        ("absorption", "absorption", "AbsorptionRester"),
        ("alloys", "alloys", "AlloysRester"),
        ("bonds", "bonds", "BondsRester"),
        (
            "chemenv",
            "chemenv",
            "ChemenvRester",
        ),
        ("conversion_electrodes", "electrodes", "ConversionElectrodeRester"),
        ("dielectric", "dielectric", "DielectricRester"),
        ("doi", "doi", "DOIRester"),
        ("elasticity", "elasticity", "ElasticityRester"),
        ("electronic_structure", "electronic_structure", "ElectronicStructureRester"),
        (
            "electronic_structure_bandstructure",
            "electronic_structure",
            "BandStructureRester",
        ),
        ("electronic_structure_dos", "electronic_structure", "DosRester"),
        ("eos", "eos", "EOSRester"),
        ("grain_boundaries", "grain_boundaries", "GrainBoundaryRester"),
        ("insertion_electrodes", "electrodes", "ElectrodeRester"),
        ("magnetism", "magnetism", "MagnetismRester"),
        ("oxidation_states", "oxidation_states", "OxidationStatesRester"),
        ("phonon", "phonon", "PhononRester"),
        ("piezoelectric", "piezo", "PiezoRester"),
        ("provenance", "provenance", "ProvenanceRester"),
        ("robocrys", "robocrys", "RobocrysRester"),
        ("similarity", "similarity", "SimilarityRester"),
        ("substrates", "substrates", "SubstratesRester"),
        ("summary", "summary", "SummaryRester"),
        ("surface_properties", "surface_properties", "SurfacePropertiesRester"),
        ("synthesis", "synthesis", "SynthesisRester"),
        ("tasks", "tasks", "TaskRester"),
        ("thermo", "thermo", "ThermoRester"),
        ("xas", "xas", "XASRester"),
    )
}
