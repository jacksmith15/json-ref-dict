import pytest

from json_ref_dict.ref_dict import RefDict
from json_ref_dict.materialize import materialize


pytestmark = pytest.mark.materialize


def test_materialize_document():
    ref_dict = RefDict("tests/schemas/master.yaml#/")
    dictionary = materialize(ref_dict)
    assert isinstance(dictionary, dict)
    assert dictionary == {
        "definitions": {
            "foo": {"type": "string"},
            "local_ref": {"type": "string"},
            "remote_ref": {"type": "integer"},
            "backref": {"type": "string"},
        }
    }


def test_materialize_circular_ref():
    ref_dict = RefDict("tests/schemas/circular.yaml#/")
    dictionary = materialize(ref_dict)
    assert isinstance(dictionary, dict)
    assert (
        dictionary["definitions"]
        == dictionary["definitions"]["foo"]["definitions"]
    )
