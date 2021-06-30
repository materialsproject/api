from enum import Enum
from random import choice, randint

import pytest
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from mp_api.core.api import MAPI

from maggma.api.resource import ReadOnlyResource
from maggma.stores import MemoryStore


class PetType(str, Enum):
    cat = "cat"
    dog = "dog"


class Owner(BaseModel):
    name: str = Field(..., title="Owner's name")
    age: int = Field(..., title="Owne'r Age")
    weight: int = Field(..., title="Owner's weight")


class Pet(BaseModel):
    name: str = Field(..., title="Pet's Name")
    pet_type: PetType = Field(..., title="Pet Type")
    owner_name: str = Field(..., title="Owner's name")


owners = [
    Owner(name=f"Person{i}", age=randint(10, 100), weight=randint(100, 200))
    for i in list(range(10))
]


pets = [
    Pet(name=f"Pet{i}", pet_type=choice(list(PetType)), owner_name=choice(owners).name,)
    for i in list(range(40))
]


@pytest.fixture
def owner_store():
    store = MemoryStore("owners", key="name")
    store.connect()
    store.update([jsonable_encoder(d) for d in owners])
    return store


@pytest.fixture
def pet_store():
    store = MemoryStore("pets", key="name")
    store.connect()
    store.update([jsonable_encoder(d) for d in pets])
    return store


def test_mapi(owner_store, pet_store):
    owner_endpoint = ReadOnlyResource(owner_store, Owner)
    pet_endpoint = ReadOnlyResource(pet_store, Pet)

    manager = MAPI({"owners": [owner_endpoint], "pets": [pet_endpoint]})

    api_dict = manager.as_dict()

    for k in ["@class", "@module", "resources"]:
        assert k in api_dict

    assert manager.app.openapi()["components"]["securitySchemes"] == {
        "ApiKeyAuth": {
            "descriptions": "MP API key to authorize requests",
            "name": "X-API-KEY",
            "in": "header",
            "type": "apiKey",
        }
    }
