from typing import Callable

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


name_label: Callable = lambda ref: ("title", ref.split("/")[-1] or "#")
uri_label: Callable = lambda ref: ("uri", ref)


def test_materialize_name_label():
    ref_dict = RefDict("tests/schemas/master.yaml#/")
    dictionary = materialize(ref_dict, context_labeller=name_label)
    assert isinstance(dictionary, dict)
    assert dictionary == {
        "definitions": {
            "title": "definitions",
            "foo": {"type": "string", "title": "foo"},
            "local_ref": {"type": "string", "title": "foo"},
            "remote_ref": {"type": "integer", "title": "bar"},
            "backref": {"type": "string", "title": "foo"},
        },
        "title": "#",
    }


def test_materialize_uri_label():
    ref_dict = RefDict("tests/schemas/master.yaml#/")
    dictionary = materialize(ref_dict, context_labeller=uri_label)
    assert isinstance(dictionary, dict)
    assert dictionary == {
        "uri": "tests/schemas/master.yaml#/",
        "definitions": {
            "uri": "tests/schemas/master.yaml#/definitions",
            "foo": {
                "type": "string",
                "uri": "tests/schemas/master.yaml#/definitions/foo",
            },
            "local_ref": {
                "type": "string",
                "uri": "tests/schemas/master.yaml#/definitions/foo",
            },
            "remote_ref": {
                "type": "integer",
                "uri": "tests/schemas/other.yaml#/definitions/bar",
            },
            "backref": {
                "type": "string",
                "uri": "tests/schemas/master.yaml#/definitions/foo",
            },
        },
    }


def test_materialize_name_label_circular():
    ref_dict = RefDict("tests/schemas/circular.yaml#/")
    dictionary = materialize(ref_dict, context_labeller=name_label)
    assert isinstance(dictionary, dict)
    assert dictionary["definitions"]["title"] == "definitions"
    assert dictionary["definitions"]["foo"]["title"] == "#"


def test_materialize_recursive_files():
    ref_dict = RefDict("tests/schemas/recursive_depth0.yaml#/")
    dictionary = materialize(ref_dict)
    assert isinstance(dictionary, dict)
    assert dictionary == {
        "definitions": {"local_ref": {"sublevel": {"type": "string"}}}
    }


def test_materialize_slash_key():
    ref_dict = RefDict("tests/schemas/slash-key.yaml#/")
    dictionary = materialize(ref_dict)
    assert isinstance(dictionary, dict)
    assert dictionary == {
        "definitions": {
            "bar/baz": {"type": "integer"},
            "key_with_slashpath": {"foo/bar": {"baz": {"type": "integer"}}},
            "nested_reference": {"foo/bar": {"baz": {"type": "integer"}}},
            "slash_key": {"type": "integer"},
            "slash_key_recursion": {"foo/bar": {"baz": {"type": "integer"}}},
        }
    }
