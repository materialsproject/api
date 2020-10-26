import os
from monty.serialization import loadfn
from mp_api.core.api import MAPI

resources = {}

db_uri = os.environ.get("MPCONTRIBS_MONGO_HOST", None)
db_version = os.environ.get("DB_VERSION")

# Uncomment to use JSON store for development
# core_store = JSONStore("./test_files/materials_Li_Fe_V.json")
# task_store = JSONStore("./test_files/tasks_Li_Fe_V.json")

materials_store_json = os.environ.get("MATERIALS_STORE", "materials_store.json")
task_store_json = os.environ.get("TASK_STORE", "task_store.json")
thermo_store_json = os.environ.get("THERMO_STORE", "thermo_store.json")
eos_store_json = os.environ.get("EOS_STORE", "eos_store.json")
similarity_store_json = os.environ.get("SIMILARITY_STORE", "similarity_store.json")
xas_store_json = os.environ.get("XAS_STORE", "xas_store.json")
gb_store_json = os.environ.get("GB_STORE", "xas_store.json")
fermi_store_json = os.environ.get("FERMI_STORE", "fermi_store.json")
doi_store_json = os.environ.get("DOI_STORE", "doi_store.json")
substrates_store_json = os.environ.get("SUBSTRATES_STORE", "substrates_store.json")
surface_props_store_json = os.environ.get(
    "SURFACE_PROPS_STORE", "surface_props_store.json"
)
wulff_store_json = os.environ.get("WULFF_STORE", "wulff_store.json")

bs_store_json = os.environ.get("BS_STORE", "bs_store.json")
dos_store_json = os.environ.get("DOS_STORE", "dos_store.json")

s3_bs_index_json = os.environ.get("S3_BS_INDEX_STORE", "s3_bs_index.json")
s3_dos_index_json = os.environ.get("S3_DOS_INDEX_STORE", "s3_dos_index.json")

s3_bs_json = os.environ.get("S3_BS_STORE", "s3_bs.json")
s3_dos_json = os.environ.get("S3_DOS_STORE", "s3_dos.json")

if db_uri:
    from maggma.stores import MongoURIStore, S3Store

    materials_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name=f"materials.core_{db_version}",
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
        key="task_id",
        collection_name=f"thermo_{db_version}",
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
        key="task_id",
        collection_name="similarity",
    )

    xas_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="xas_id",
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

    wulff_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="wulff",
    )

    bs_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="bandstructure",
    )

    s3_bs_index = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="s3_bandstructure_index",
    )

    dos_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="dos",
    )

    s3_dos_index = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="s3_dos_index",
    )

    s3_bs = S3Store(index=s3_bs_index, bucket="mp-bandstructures", compress=True)

    s3_dos = S3Store(index=s3_dos_index, bucket="mp-dos", compress=True)


else:
    materials_store = loadfn(materials_store_json)
    task_store = loadfn(task_store_json)
    thermo_store = loadfn(thermo_store_json)
    eos_store = loadfn(eos_store_json)
    similarity_store = loadfn(similarity_store_json)
    xas_store = loadfn(xas_store_json)
    gb_store = loadfn(gb_store_json)
    fermi_store = loadfn(fermi_store_json)
    doi_store = loadfn(doi_store_json)
    substrates_store = loadfn(substrates_store_json)
    surface_props_store = loadfn(surface_props_store_json)
    wulff_store = loadfn(wulff_store_json)

    bs_store = loadfn(bs_store_json)
    dos_store = loadfn(dos_store_json)
    s3_bs_index = loadfn(s3_bs_index_json)
    s3_dos_index = loadfn(s3_dos_index_json)
    s3_bs = loadfn(s3_bs_json)
    s3_dos = loadfn(s3_dos_json)

# Materials
from mp_api.materials.resources import materials_resource

resources.update({"materials": materials_resource(materials_store)})

# Tasks
from mp_api.tasks.resources import task_resource

resources.update({"tasks": task_resource(task_store)})

# Task Deprecation
from mp_api.tasks.resources import task_deprecation_resource

resources.update({"deprecation": task_deprecation_resource(materials_store)})

# Trajectory
from mp_api.tasks.resources import trajectory_resource

resources.update({"trajectory": trajectory_resource(task_store)})

# Thermo
from mp_api.thermo.resources import thermo_resource

resources.update({"thermo": thermo_resource(thermo_store)})

# EOS
from mp_api.eos.resources import eos_resource

resources.update({"eos": eos_resource(eos_store)})

# Similarity
from mp_api.similarity.resources import similarity_resource

resources.update({"similarity": similarity_resource(similarity_store)})

# XAS
from mp_api.xas.resources import xas_resource

resources.update({"xas": xas_resource(xas_store)})

# Grain Boundaries
from mp_api.gb.resources import gb_resource

resources.update({"gb": gb_resource(gb_store)})

# Fermi Surface
from mp_api.fermi.resources import fermi_resource

resources.update({"fermi": fermi_resource(fermi_store)})

# DOIs
from mp_api.dois.resources import dois_resource

resources.update({"doi": dois_resource(doi_store)})

# Substrates
from mp_api.substrates.resources import substrates_resource

resources.update({"substrates": substrates_resource(substrates_store)})

# Surface Properties
from mp_api.surface_properties.resources import surface_props_resource

resources.update({"surface_properties": surface_props_resource(surface_props_store)})

# Surface Properties
from mp_api.wulff.resources import wulff_resource

resources.update({"wulff": wulff_resource(wulff_store)})


# Band Structure
from mp_api.bandstructure.resources import bs_resource

resources.update({"bs": bs_resource(bs_store, s3_bs)})

# DOS
from mp_api.dos.resources import dos_resource

resources.update({"dos": dos_resource(dos_store, s3_dos)})

api = MAPI(resources=resources)
app = api.app
