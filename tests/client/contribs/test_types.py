"""Test MPContribs data types / objects."""

import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from mp_api.client.contribs._types import Attachment, MPCDict, Table
from mp_api.client.contribs.utils import _compress


def test_table():
    data = {
        "first_name": ["Todd", "Willie", "Mike"],
        "family_name": ["Bonzalez", "Dustice", "Truk"],
        "age": [31, 24, 28],
        "batting_average": [0.777, 0.5, 0.81],
    }
    test_table = Table(data)

    # Calling `as_dict` transforms the data in a `Table`
    table_as_dict = Table(test_table.copy()).as_dict()
    assert all(
        table_as_dict.get(k) for k in ("attrs", "columns", "data", "index", "name")
    )
    table_info = test_table.info()
    assert {y.strip() for y in table_info["columns"].split(",")} == set(
        test_table.columns
    )
    assert table_info["nrows"] == len(test_table)

    table_roundtrip = Table.from_dict(table_as_dict)

    # `tolist()` needed to compare base python types
    for t in (test_table, table_roundtrip):
        assert all(
            isinstance(v, str)
            for col in ("family_name", "first_name")
            for v in t[col].tolist()
        )
        assert all(isinstance(v, int) for v in t.age.tolist())
        assert all(isinstance(v, float) for v in t.batting_average.tolist())


def test_attachment():
    data_struct = {
        "foo": ["bar", "baz"],
        "lorem": {
            "ipsum": 1.0,
            "dolor": 3.0,
            "sit": 5.0,
            "amet": 7.0,
        },
        "more": None,
    }

    attachment = Attachment.from_data(data_struct, name="test_data")
    assert isinstance(attachment, dict)
    assert all(isinstance(attachment.get(k), str) for k in ("name", "mime", "content"))
    assert attachment.name == "test_data.json.gz"
    assert attachment["mime"] == "application/gzip"

    assert attachment.info() == {
        **{k: attachment[k] for k in ("name", "mime")},
        "size": _compress(data_struct)[0],
    }
    assert isinstance(attachment.info(), MPCDict)

    # Test roundtrip data
    assert json.loads(attachment.unpack()) == data_struct

    # Test writeout + loading from file
    with TemporaryDirectory() as temp_dir:
        attachment.write(outdir=temp_dir)
        # Attachment can't read from gzipped output, so we ungzip first
        not_gzipped = Path(temp_dir) / attachment.name.split(".gz")[0]
        with (
            gzip.open(Path(temp_dir) / attachment.name, "rb") as f_in,
            open(not_gzipped, "wb") as f_out,
        ):
            f_out.write(f_in.read())

        # create a copy of the original attachment from the non-gzipped file
        new_attach = Attachment.from_file(not_gzipped)

    # Finally test roundtrip
    assert json.loads(new_attach.unpack()) == data_struct
