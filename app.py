import os
from monty.serialization import loadfn
from fastapi import FastAPI
import mp_api.xas.api


xas_store = os.environ.get("XAS_STORE", "xas_store.json")
xas_store = loadfn(xas_store)
xas_router = mp_api.xas.api.get_router(xas_store)

app = FastAPI(title="Materials Project API", version="3.0.0-dev")
app.include_router(xas_router)
