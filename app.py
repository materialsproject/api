import os
from monty.serialization import loadfn

from mp_api.core.api import MAPI
from mp_api.core.settings import MAPISettings

resources = {}

default_settings = MAPISettings()

db_uri = os.environ.get("MPCONTRIBS_MONGO_HOST", None)
db_version = os.environ.get("DB_VERSION", default_settings.db_version)
debug = os.environ.get("API_DEBUG", default_settings.debug)

materials_store_json = os.environ.get("MATERIALS_STORE", "materials_store.json")
formula_autocomplete_store_json = os.environ.get(
    "FORMULA_AUTOCOMPLETE_STORE", "formula_autocomplete_store.json"
)
task_store_json = os.environ.get("TASK_STORE", "task_store.json")
thermo_store_json = os.environ.get("THERMO_STORE", "thermo_store.json")
dielectric_piezo_store_json = os.environ.get(
    "DIELECTRIC_PIEZO_STORE", "dielectric_piezo_store.json"
)
magnetism_store_json = os.environ.get("MAGNETISM_STORE", "magnetism_store.json")
phonon_bs_store_json = os.environ.get("PHONON_BS_STORE", "phonon_bs_store.json")
eos_store_json = os.environ.get("EOS_STORE", "eos_store.json")
similarity_store_json = os.environ.get("SIMILARITY_STORE", "similarity_store.json")
xas_store_json = os.environ.get("XAS_STORE", "xas_store.json")
gb_store_json = os.environ.get("GB_STORE", "xas_store.json")
fermi_store_json = os.environ.get("FERMI_STORE", "fermi_store.json")
elasticity_store_json = os.environ.get("ELASTICITY_STORE", "elasticity_store.json")
doi_store_json = os.environ.get("DOI_STORE", "doi_store.json")
substrates_store_json = os.environ.get("SUBSTRATES_STORE", "substrates_store.json")
surface_props_store_json = os.environ.get(
    "SURFACE_PROPS_STORE", "surface_props_store.json"
)
robocrys_store_json = os.environ.get("ROBOCRYS_STORE", "robocrys_store.json")
synth_store_json = os.environ.get("SYNTH_STORE", "synth_store.json")
insertion_electrodes_store_json = os.environ.get(
    "INSERTION_ELECTRODES_STORE", "insertion_electrodes_store.json"
)
molecules_store_json = os.environ.get("MOLECULES_STORE", "molecules_store.json")
oxi_states_store_json = os.environ.get("OXI_STATES_STORE", "oxi_states_store.json")
provenance_store_json = os.environ.get("PROVENANCE_STORE", "provenance_store.json")
summary_store_json = os.environ.get("SUMMARY_STORE", "summary_store.json")

es_store_json = os.environ.get("ES_STORE", "es_store.json")

bs_store_json = os.environ.get("BS_STORE", "bs_store.json")
dos_store_json = os.environ.get("DOS_STORE", "dos_store.json")

s3_bs_index_json = os.environ.get("S3_BS_INDEX_STORE", "s3_bs_index.json")
s3_dos_index_json = os.environ.get("S3_DOS_INDEX_STORE", "s3_dos_index.json")

s3_bs_json = os.environ.get("S3_BS_STORE", "s3_bs.json")
s3_dos_json = os.environ.get("S3_DOS_STORE", "s3_dos.json")

s3_chgcar_index_json = os.environ.get("CHGCAR_INDEX_STORE", "chgcar_index_store.json")
s3_chgcar_json = os.environ.get("S3_CHGCAR_STORE", "s3_chgcar.json")

mpcomplete_store_json = os.environ.get("MPCOMPLETE_STORE", "mpcomplete_store.json")

consumer_settings_store_json = os.environ.get(
    "CONSUMER_SETTINGS_STORE", "consumer_settings_store.json"
)


if db_uri:
    from maggma.stores import MongoURIStore, S3Store

    materials_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="material_id",
        collection_name=f"materials.core_{db_version}",
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
        database="mp_core",
        key="material_id",
        collection_name=f"thermo_{db_version}",
    )

    dielectric_piezo_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="dielectric",
    )

    magnetism_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
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
        database="mp_core",
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
        database="mp_core",
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
        database="mp_core",
        key="material_id",
        collection_name="oxi_states",
    )

    provenance_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="material_id",
        collection_name="provenance",
    )

    summary_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="material_id",
        collection_name="summary",
    )

    es_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
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

else:
    materials_store = loadfn(materials_store_json)
    formula_autocomplete_store = loadfn(formula_autocomplete_store_json)
    task_store = loadfn(task_store_json)
    thermo_store = loadfn(thermo_store_json)
    dielectric_piezo_store = loadfn(dielectric_piezo_store_json)
    magnetism_store = loadfn(magnetism_store_json)
    phonon_bs_store = loadfn(phonon_bs_store_json)
    eos_store = loadfn(eos_store_json)
    similarity_store = loadfn(similarity_store_json)
    xas_store = loadfn(xas_store_json)
    gb_store = loadfn(gb_store_json)
    fermi_store = loadfn(fermi_store_json)
    elasticity_store = loadfn(elasticity_store_json)
    doi_store = loadfn(doi_store_json)
    substrates_store = loadfn(substrates_store_json)
    surface_props_store = loadfn(surface_props_store_json)
    robo_store = loadfn(robocrys_store_json)
    synth_store = loadfn(synth_store_json)
    insertion_electrodes_store = loadfn(insertion_electrodes_store_json)
    molecules_store = loadfn(molecules_store_json)
    oxi_states_store = loadfn(oxi_states_store_json)
    provenance_store = loadfn(provenance_store_json)
    summary_store = loadfn(summary_store_json)

    es_store = loadfn(es_store_json)

    s3_bs_index = loadfn(s3_bs_index_json)
    s3_dos_index = loadfn(s3_dos_index_json)
    s3_bs = loadfn(s3_bs_json)
    s3_dos = loadfn(s3_dos_json)

    s3_chgcar_index = loadfn(s3_chgcar_index_json)
    s3_chgcar = loadfn(s3_chgcar_json)

    mpcomplete_store = loadfn(mpcomplete_store_json)
    consumer_settings_store = loadfn(consumer_settings_store_json)

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

# resources.update({"find_structure": find_structure_resource(materials_store)})

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
from mp_api.routes.thermo.resources import thermo_resource

resources.update({"thermo": [thermo_resource(thermo_store)]})

# Dielectric
from mp_api.routes.dielectric.resources import dielectric_resource

resources.update({"dielectric": [dielectric_resource(dielectric_piezo_store)]})

# Magnetism
from mp_api.routes.magnetism.resources import magnetism_resource

resources.update({"magnetism": [magnetism_resource(magnetism_store)]})

# Piezoelectric
from mp_api.routes.piezo.resources import piezo_resource

resources.update({"piezoelectric": [piezo_resource(dielectric_piezo_store)]})

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

# === MAPI setup
from mp_api.core.documentation import description, tags_meta

api = MAPI(
    resources=resources, debug=debug, description=description, tags_meta=tags_meta
)
app = api.app
