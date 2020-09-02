import os
from monty.serialization import loadfn
from mp_api.core.api import MAPI

resources = {}

db_uri = os.environ.get("MPCONTRIBS_MONGO_HOST", None)

# Uncomment to use JSON store for development
# core_store = JSONStore("./test_files/materials_Li_Fe_V.json")
# task_store = JSONStore("./test_files/tasks_Li_Fe_V.json")

core_store_json = os.environ.get("CORE_STORE", "core_store.json")
task_store_json = os.environ.get("TASK_STORE", "task_store.json")
xas_store_json = os.environ.get("XAS_STORE", "xas_store.json")

if db_uri:
    from maggma.stores import MongoURIStore

    core_store = MongoURIStore(
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

    xas_store = MongoURIStore(
        uri=f"mongodb+srv://{db_uri}",
        database="mp_core",
        key="xas_id",
        collection_name="xas",
    )
else:
    core_store = loadfn(core_store_json)
    task_store = loadfn(task_store_json)
    xas_store = loadfn(xas_store_json)

# Materials
from mp_api.materials.resources import core_resource

resources.update({"core": core_resource(core_store)})

# Tasks
from mp_api.tasks.resources import task_resource

resources.update({"tasks": task_resource(task_store)})

# Trajectory
from mp_api.tasks.resources import trajectory_resource

resources.update({"trajectory": trajectory_resource(task_store)})

# XAS
from mp_api.xas.resources import xas_resource

resources.update({"xas": xas_resource(xas_store)})


api = MAPI(resources=resources)
app = api.app
