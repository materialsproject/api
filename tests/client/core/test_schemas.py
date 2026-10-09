"""Test core schemas."""

from itertools import product
from pydantic import BaseModel
import pytest

from mp_api.client.core.schemas import _DictLikeAccess, _convert_to_model


class DummyClass(_DictLikeAccess):
    a: int
    b: float
    c: list[str]


def test_dict_like_access():
    instance = DummyClass(a=1, b=2.0, c=["a", "b", "c"])
    assert isinstance(instance, BaseModel)
    assert all(
        getattr(instance, field_name) == instance[field_name]
        and instance[field_name] == instance.get(field_name)
        for field_name in DummyClass.model_fields
    )

    as_str = """DummyClass(
  a (int) : 1
  b (float) : 2.0
  c (list) : ['a', 'b', 'c']
)"""
    assert str(instance) == as_str
    assert repr(instance) == as_str

    with pytest.raises(
        AttributeError, match="'DummyClass' object has no attribute 'd'"
    ):
        instance.d
    assert instance.get("d", None) == None


def test_model_generation():
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
        as_models = _convert_to_model(trial_data, DummyClass, model_name=test_type)
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
                for k in DummyClass.model_fields
                for doc in as_models
            )

        assert all(
            substr in str(doc)
            for substr in ("Fields not requested", "DummyClass", test_type)
            for doc in as_models
        )

    # Test requesting unavailable fields
    as_models = _convert_to_model(
        [{k: v for k, v in doc.items() if k != "b"} for doc in get_data()],
        DummyClass,
        requested_fields=["b"],
    )

    with pytest.raises(AttributeError, match="`b` is unavailable in the returned data"):
        as_models[0].b

    # Test accessing fields that weren't requested
    as_models = _convert_to_model(
        [{k: v for k, v in doc.items() if k == "b"} for doc in get_data()],
        DummyClass,
        requested_fields=["b"],
    )
    with pytest.raises(
        AttributeError, match="`a` data is available but has not been requested"
    ):
        as_models[0].a

    # Ensure graceful handling of empty iterator input (no docs returned)
    assert _convert_to_model(iter([]), DummyClass) == []


def test_returned_model_repr_is_plain_and_rich_is_styled():
    import io

    from rich.console import Console

    from mp_api.client.core.schemas import _generate_returned_model

    class Doc(BaseModel):
        material_id: str | None = None
        band_gap: float | None = None
        formula: str | None = None

    model, _, _ = _generate_returned_model(
        {"material_id": "mp-149", "band_gap": 1.1}, Doc
    )
    doc = model(material_id="mp-149", band_gap=1.1)

    for text in (repr(doc), str(doc)):
        assert "\x1b[" not in text
        assert "MPDataDoc<Doc>" in text and "band_gap=1.1" in text
    assert "fields_not_requested=['formula']" in repr(doc)
    assert "Fields not requested:" in str(doc)

    buf = io.StringIO()
    Console(file=buf, force_terminal=True, width=100).print(doc)
    out = buf.getvalue()
    assert "\x1b[1;4mMPDataDoc<Doc>" in out  # bold underline title
    assert "material_id" in out and "'mp-149'" in out
