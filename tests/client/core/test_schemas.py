"""Test core schemas."""

from itertools import product
from pydantic import BaseModel
import pytest

from mp_api.client.core.schemas import _DictLikeAccess, _convert_to_model


class TestClass(_DictLikeAccess):
    a: int
    b: float
    c: list[str]


def test_dict_like_access():
    instance = TestClass(a=1, b=2.0, c=["a", "b", "c"])
    assert isinstance(instance, BaseModel)
    assert all(
        getattr(instance, field_name) == instance[field_name]
        and instance[field_name] == instance.get(field_name)
        for field_name in TestClass.model_fields
    )

    as_str = """TestClass(
  a (int) : 1
  b (float) : 2.0
  c (list) : ['a', 'b', 'c']
)"""
    assert str(instance) == as_str
    assert repr(instance) == as_str

    with pytest.raises(AttributeError, match="'TestClass' object has no attribute 'd'"):
        instance.d
    assert instance.get("d", None) == None


def test_generate_model():
    a_vals = [1, 2]
    b_vals = [5.0, 7.0]
    c_vals = [
        ["foo", "bar"],
        ["baz"],
    ]
    get_data = lambda: (
        {"a": a, "b": b, "c": c} for a in a_vals for b in b_vals for c in c_vals
    )

    for test_type, trial_data in {
        "iterator": get_data(),
        "list": list(get_data()),
        "iterator_with_missing": (
            {k: v for k, v in doc.items() if k != "b"} for doc in get_data()
        ),
    }.items():
        as_models = _convert_to_model(trial_data, TestClass, model_name=test_type)
        assert all(isinstance(doc, BaseModel) for doc in as_models)
        assert all(doc.__class__.__name__ == test_type for doc in as_models)

        with pytest.raises(
            AttributeError, match=f"{test_type!r} object has no attribute 'd'"
        ):
            as_models[0].d

        if test_type == "iterator_with_missing":
            assert all(
                doc.get(k) is not None
                and doc.get("b") is None
                and doc.fields_not_requested == ["b"]
                for doc in as_models
                for k in ("a", "c")
            )
        else:
            assert all(
                getattr(doc, k) and doc.get(k)
                for k in TestClass.model_fields
                for doc in as_models
            )

        assert all(
            substr in str(doc)
            for substr in ("Fields not requested", "TestClass", test_type)
            for doc in as_models
        )

    # Test requesting unavailable fields
    as_models = _convert_to_model(
        [{k: v for k, v in doc.items() if k != "b"} for doc in get_data()],
        TestClass,
        requested_fields=["b"],
    )

    with pytest.raises(AttributeError, match="`b` is unavailable in the returned data"):
        as_models[0].b

    # Test accessing fields that weren't requested
    as_models = _convert_to_model(
        [{k: v for k, v in doc.items() if k == "b"} for doc in get_data()],
        TestClass,
        requested_fields=["b"],
    )
    with pytest.raises(
        AttributeError, match="`a` data is available but has not been requested"
    ):
        as_models[0].a
