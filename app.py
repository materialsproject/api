import os
from monty.serialization import loadfn
from mp_api.core.api import MAPI

resources = {}

db_uri = os.environ.get("MPCONTRIBS_MONGO_HOST", None)

# Uncomment to use JSON store for development
# core_store = JSONStore("./test_files/materials_Li_Fe_V.json")
# task_store = JSONStore("./test_files/tasks_Li_Fe_V.json")

materials_store_json = os.environ.get("MATERIALS_STORE", "materials_store.json")
task_store_json = os.environ.get("TASK_STORE", "task_store.json")
eos_store_json = os.environ.get("EOS_STORE", "eos_store.json")
similarity_store_json = os.environ.get("SIMILARITY_STORE", "similarity_store.json")
xas_store_json = os.environ.get("XAS_STORE", "xas_store.json")

if db_uri:
    from maggma.stores import MongoURIStore

    materials_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="materials.core",
    )

    task_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="task_id",
        collection_name="tasks",
    )

    eos_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="mp_id",
        collection_name="eos",
    )

    similarity_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="mid",
        collection_name="similarity",
    )

    xas_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="xas_id",
        collection_name="xas",
    )
else:
    materials_store = loadfn(materials_store_json)
    task_store = loadfn(task_store_json)
    eos_store = loadfn(eos_store_json)
    similarity_store = loadfn(similarity_store_json)
    xas_store = loadfn(xas_store_json)

# Materials
from mp_api.materials.resources import materials_resource

resources.update({"materials": materials_resource(materials_store)})

# Tasks
from mp_api.tasks.resources import task_resource

resources.update({"tasks": task_resource(task_store)})

# Trajectory
from mp_api.tasks.resources import trajectory_resource

resources.update({"trajectory": trajectory_resource(task_store)})

# EOS
from mp_api.eos.resources import eos_resource

resources.update({"eos": eos_resource(eos_store)})

# Similarity
from mp_api.similarity.resources import similarity_resource

resources.update({"similarity": similarity_resource(similarity_store)})

# XAS
from mp_api.xas.resources import xas_resource

resources.update({"xas": xas_resource(xas_store)})


api = MAPI(resources=resources)
app = api.app
