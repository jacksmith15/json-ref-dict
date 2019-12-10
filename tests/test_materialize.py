from json_ref_dict.ref_dict import RefDict
from json_ref_dict.materialize import materialize


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


def test_materialize_array():
    ref_dict = RefDict("tests/schemas/array-ref.yaml#/")
    dictionary = materialize(ref_dict)
    assert isinstance(dictionary, dict)
    assert dictionary == {
        "definitions": {
            "foo": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            "bar": {"type": "string"},
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


def test_materialize_document_exclude_keys():
    ref_dict = RefDict("tests/schemas/master.yaml#/")
    dictionary = materialize(ref_dict, exclude_keys={"remote_ref"})
    assert isinstance(dictionary, dict)
    assert dictionary == {
        "definitions": {
            "foo": {"type": "string"},
            "local_ref": {"type": "string"},
            "backref": {"type": "string"},
        }
    }


def test_materialize_document_include_keys():
    ref_dict = RefDict("tests/schemas/master.yaml#/")
    dictionary = materialize(
        ref_dict, include_keys={"remote_ref", "definitions", "type"}
    )
    assert isinstance(dictionary, dict)
    assert dictionary == {"definitions": {"remote_ref": {"type": "integer"}}}


def test_materialize_document_value_map():
    ref_dict = RefDict("tests/schemas/master.yaml#/")
    dictionary = materialize(ref_dict, value_map=len)
    assert isinstance(dictionary, dict)
    assert dictionary == {
        "definitions": {
            "foo": {"type": 6},
            "local_ref": {"type": 6},
            "remote_ref": {"type": 7},
            "backref": {"type": 6},
        }
    }
