"""Test schemas and schema-related utilities for contribs."""

from datetime import datetime
import numpy as np
import pandas as pd
from pydantic import BaseModel
import pytest
from typing import Any

from mp_api.client.contribs.schemas import (
    _get_unit,
    _to_camel_case,
    _get_pydantic_from_dataframe,
    ContribSubmission,
    Datum,
)


@pytest.fixture
def sample_data() -> pd.DataFrame:
    _data = {
        "Temperature [K]": np.linspace(100.0, 500.0, 50),
        "Energy (eV/atom)": np.linspace(-2.0, 3, 50),
        "Formation Energy (eV/atom)": np.linspace(-5.0, 0.1, 50),
    }
    _data["is_stable"] = _data["Formation Energy (eV/atom)"] < 0.0
    df = pd.DataFrame(_data)

    def interpret(v):
        if v < 0.0:
            return "stable"
        elif v < 0.1:
            return "meta-stable"
        else:
            return "unstable"

    # Add string data with a missing value
    df["interpretation"] = df["Formation Energy (eV/atom)"].apply(interpret)
    df.loc[len(df) - 1, "interpretation"] = None

    return df


def test_get_unit_and_val():
    assert all(
        _get_unit(entry) == (expected_value, expected_unit)
        for (entry, expected_value, expected_unit) in [
            ("Entropy (J/K)", "Entropy", "J/K"),
            ("Proton number", "Proton number", None),
            ("Pressure [GPa]", "Pressure", "GPa"),
            ("Energy [g.cm^2/s]", "Energy", "g.cm^2/s"),
        ]
    )


def test_snake_to_camel():
    assert all(
        _to_camel_case(test_str) == expected_str
        for test_str, expected_str in [
            ("this_is_a_test", "ThisIsATest"),
            ("hello my clementine", "HelloMyClementine"),
            ("I_aM_a_PaTHolOgiCal_c4SE", "IAmAPathologicalC4se"),
        ]
    )


def test_pydantic_from_pandas(sample_data):
    base_model, col_map = _get_pydantic_from_dataframe(sample_data)

    assert all(
        base_model.model_fields[camel_col].description == _get_unit(old_col)[1]
        for old_col, camel_col in col_map.items()
    )

    float_type_cols = ("Temperature", "Energy", "FormationEnergy")
    expected_col_types = {
        "IsStable": bool,
        "Interpretation": str | None,
        **{k: float for k in float_type_cols},
    }

    # Test that column names and units are properly parsed / converted to CamelCase
    assert all(
        field.annotation == expected_col_types[camel_col]
        for camel_col, field in base_model.model_fields.items()
    )

    # Now test that the document model actually works
    # Should permit dict-like key access
    rows = [row.to_dict() for _, row in sample_data.iterrows()]
    docs = [
        base_model(
            **{camel_col: row_dict[old_col] for old_col, camel_col in col_map.items()}
        )
        for row_dict in rows
    ]
    assert all(
        isinstance(doc, BaseModel) and isinstance(doc, base_model) for doc in docs
    )

    for old_col, camel_col in col_map.items():
        if camel_col in (expected_col_types):
            assert [doc[camel_col] for doc in docs] == pytest.approx(
                sample_data[old_col].tolist()
            )
        else:
            assert [doc[camel_col] for doc in docs] == sample_data[old_col].tolist()


def test_contrib_submission_from_pandas(sample_data):
    base_model, col_map = _get_pydantic_from_dataframe(sample_data)
    new_to_old_col = {v: k for k, v in col_map.items()}
    unit_map = {k: field.description for k, field in base_model.model_fields.items()}

    contributions = ContribSubmission.from_dataframe(sample_data)
    assert all(isinstance(contrib, ContribSubmission) for contrib in contributions)
    assert all(
        isinstance(contrib["last_modified"], datetime) for contrib in contributions
    )

    # Test safe placeholders / defaults:
    assert [contrib.identifier for contrib in contributions] == [
        str(v) for v in range(len(contributions))
    ]
    assert all(not contrib.is_public for contrib in contributions)
    assert all(contrib.project == "PLACEHOLDER" for contrib in contributions)

    float_type_cols = ("Temperature", "Energy", "FormationEnergy")
    assert all(
        isinstance(contrib.data[k], Datum) and contrib.data[k].unit == unit_map[k]
        for k in float_type_cols
        for contrib in contributions
    )
    assert all(
        [contrib["data"][k].value for contrib in contributions]
        == pytest.approx(sample_data[new_to_old_col[k]])
        for k in float_type_cols
    )

    assert all(
        contrib["data"][k] == sample_data[new_to_old_col[k]][idx]
        for idx, contrib in enumerate(contributions)
        for k in ("IsStable", "Interpretation")
    )

    # Test that these are JSONable
    assert all(isinstance(contrib.model_dump_json(), str) for contrib in contributions)


def test_datum_display():
    for value, error, unit, expected in [
        (5, 0.1, "m", "5 ± 0.1 m"),
        (13, None, "", "13"),
        (10.0, None, "cm^2", "10.0 cm^2"),
        (0.1, 0.5, "", "0.1 ± 0.5"),
    ]:
        d = Datum(value=value, error=error, unit=unit)
        assert all(v == expected for v in (d.display_name, str(d), repr(d)))
        assert d["value"] == pytest.approx(value)
        assert d["error"] == pytest.approx(error)
