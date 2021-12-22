import os
from monty.serialization import loadfn

from mp_api.core.api import MAPI
from mp_api.core.settings import MAPISettings
from maggma.stores import MongoURIStore, S3Store

resources = {}

default_settings = MAPISettings()

db_uri = os.environ.get("MPCONTRIBS_MONGO_HOST", None)
db_version = default_settings.DB_VERSION
db_suffix = os.environ.get("MAPI_DB_NAME_SUFFIX", db_version)
debug = default_settings.DEBUG

if db_uri:

    materials_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="materials",
    )

    bonds_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="bonds",
    )

    formula_autocomplete_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="_id",
        collection_name="formula_autocomplete",
    )

    task_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="tasks",
    )

    thermo_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="thermo",
    )

    phase_diagram_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="chemsys",
        collection_name="phase_diagram",
    )

    dielectric_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="dielectric",
    )

    piezoelectric_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="piezoelectric",
    )

    magnetism_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="magnetism",
    )

    phonon_bs_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="material_id",
        collection_name="pmg_ph_bs",
    )

    eos_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="eos",
    )

    similarity_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="material_id",
        collection_name="similarity",
    )

    xas_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="spectrum_id",
        collection_name="xas",
    )

    gb_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="grain_boundaries",
    )

    fermi_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="fermi_surface",
    )

    elasticity_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="elasticity",
    )

    doi_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="dois",
    )

    substrates_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="film_id",
        collection_name="substrates",
    )

    surface_props_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="surface_properties",
    )

    robo_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="robocrys",
    )

    synth_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="_id",
        collection_name="synth_descriptions",
    )

    insertion_electrodes_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="battery_id",
        collection_name="insertion_electrodes",
    )

    molecules_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="molecules",
    )

    oxi_states_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="oxi_states",
    )

    provenance_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="provenance",
    )

    summary_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="summary",
    )

    es_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database=f"mp_core_{db_suffix}",
        key="material_id",
        collection_name="electronic_structure",
    )

    s3_bs_index = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="fs_id",
        collection_name="s3_bandstructure_index",
    )

    s3_dos_index = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="fs_id",
        collection_name="s3_dos_index",
    )

    s3_bs = S3Store(
        index=s3_bs_index,
        bucket="mp-bandstructures",
        compress=True,
        key="fs_id",
        searchable_fields=["task_id", "fs_id"],
    )

    s3_dos = S3Store(
        index=s3_dos_index,
        bucket="mp-dos",
        compress=True,
        key="fs_id",
        searchable_fields=["task_id", "fs_id"],
    )

    s3_chgcar_index = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="fs_id",
        collection_name="atomate_chgcar_fs_index",
    )

    s3_chgcar = S3Store(
        index=s3_chgcar_index,
        bucket="mp-volumetric",
        sub_dir="atomate_chgcar_fs/",
        compress=True,
        key="fs_id",
        searchable_fields=["task_id", "fs_id"],
    )

    mpcomplete_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_consumers",
        key="submission_id",
        collection_name="mpcomplete",
    )

    consumer_settings_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_consumers",
        key="consumer_id",
        collection_name="settings",
    )

    general_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_consumers",
        key="submission_id",
        collection_name="general_store",
    )
else:
    raise RuntimeError("Must specify MongoDB Atlas URI")

# Materials
from mp_api.routes.materials.resources import (
    materials_resource,
    find_structure_resource,
    formula_autocomplete_resource,
)

resources.update(
    {
        "materials": [
            find_structure_resource(materials_store),
            formula_autocomplete_resource(formula_autocomplete_store),
            materials_resource(materials_store),
        ]
    }
)

# Bonds
from mp_api.routes.bonds.resources import bonds_resource

resources.update({"bonds": [bonds_resource(bonds_store)]})

# Tasks
from mp_api.routes.tasks.resources import (
    task_resource,
    trajectory_resource,
    task_deprecation_resource,
)

resources.update(
    {
        "tasks": [
            trajectory_resource(task_store),
            task_deprecation_resource(materials_store),
            task_resource(task_store),
        ]
    }
)

# Thermo
from mp_api.routes.thermo.resources import phase_diagram_resource, thermo_resource

resources.update(
    {
        "thermo": [
            phase_diagram_resource(phase_diagram_store),
            thermo_resource(thermo_store),
        ]
    }
)

# Dielectric
from mp_api.routes.dielectric.resources import dielectric_resource

resources.update({"dielectric": [dielectric_resource(dielectric_store)]})

# Piezoelectric
from mp_api.routes.piezo.resources import piezo_resource

resources.update({"piezoelectric": [piezo_resource(piezoelectric_store)]})

# Magnetism
from mp_api.routes.magnetism.resources import magnetism_resource

resources.update({"magnetism": [magnetism_resource(magnetism_store)]})

# Phonon
from mp_api.routes.phonon.resources import phonon_bsdos_resource

resources.update({"phonon": [phonon_bsdos_resource(phonon_bs_store)]})

# EOS
from mp_api.routes.eos.resources import eos_resource

resources.update({"eos": [eos_resource(eos_store)]})

# Similarity
from mp_api.routes.similarity.resources import similarity_resource

resources.update({"similarity": [similarity_resource(similarity_store)]})

# XAS
from mp_api.routes.xas.resources import xas_resource

resources.update({"xas": [xas_resource(xas_store)]})

# Grain Boundaries
from mp_api.routes.grain_boundary.resources import gb_resource

resources.update({"grain_boundary": [gb_resource(gb_store)]})

# Fermi Surface
from mp_api.routes.fermi.resources import fermi_resource

resources.update({"fermi": [fermi_resource(fermi_store)]})

# Elasticity
from mp_api.routes.elasticity.resources import elasticity_resource

resources.update({"elasticity": [elasticity_resource(elasticity_store)]})

# DOIs
from mp_api.routes.dois.resources import dois_resource

resources.update({"doi": [dois_resource(doi_store)]})

# Substrates
from mp_api.routes.substrates.resources import substrates_resource

resources.update({"substrates": [substrates_resource(substrates_store)]})

# Surface Properties
from mp_api.routes.surface_properties.resources import surface_props_resource

resources.update({"surface_properties": [surface_props_resource(surface_props_store)]})


# Robocrystallographer
from mp_api.routes.robocrys.resources import robo_resource, robo_search_resource

resources.update(
    {"robocrys": [robo_search_resource(robo_store), robo_resource(robo_store)]}
)

# Synthesis
from mp_api.routes.synthesis.resources import synth_resource

resources.update({"synthesis": [synth_resource(synth_store)]})

# Electrodes
from mp_api.routes.electrodes.resources import insertion_electrodes_resource

resources.update(
    {
        "insertion_electrodes": [
            insertion_electrodes_resource(insertion_electrodes_store)
        ]
    }
)

# Molecules
from mp_api.routes.molecules.resources import molecules_resource

resources.update({"molecules": [molecules_resource(molecules_store)]})

# Oxidation States
from mp_api.routes.oxidation_states.resources import oxi_states_resource

resources.update({"oxidation_states": [oxi_states_resource(oxi_states_store)]})

# Provenance
from mp_api.routes.provenance.resources import provenance_resource

resources.update({"provenance": [provenance_resource(provenance_store)]})

# Charge Density
from mp_api.routes.charge_density.resources import charge_density_resource

resources.update({"charge_density": [charge_density_resource(s3_chgcar)]})

# Summary
from mp_api.routes.summary.resources import summary_resource, summary_stats_resource

resources.update(
    {
        "summary": [
            summary_stats_resource(summary_store),
            summary_resource(summary_store),
        ]
    }
)

# Electronic Structure
from mp_api.routes.electronic_structure.resources import (
    es_resource,
    bs_resource,
    bs_obj_resource,
    dos_resource,
    dos_obj_resource,
)

resources.update(
    {
        "electronic_structure": [
            bs_resource(es_store),
            dos_resource(es_store),
            es_resource(es_store),
            bs_obj_resource(s3_bs),
            dos_obj_resource(s3_dos),
        ]
    }
)
# MPComplete
from mp_api.routes.mpcomplete.resources import mpcomplete_resource

resources.update({"mpcomplete": [mpcomplete_resource(mpcomplete_store)]})

# Consumers
from mp_api.routes._consumer.resources import settings_resource

resources.update({"_user_settings": [settings_resource(consumer_settings_store)]})

# General Store
from mp_api.routes._general_store.resources import general_store_resource

resources.update({"_general_store": [general_store_resource(general_store)]})

# === MAPI setup
from mp_api.core.documentation import description, tags_meta

api = MAPI(
    resources=resources, debug=debug, description=description, tags_meta=tags_meta
)
app = api.app
