from unittest.mock import patch

from jsonpointer import JsonPointer
import pytest

from json_ref_dict import resolve_uri, RefDict, URI


TEST_DATA = {
    "base/file1.json": {
        "definitions": {
            "foo": {"type": "string"},
            "remote_ref": {"$ref": "file2.json#/definitions/bar"},
            "local_ref": {"$ref": "#/definitions/baz"},
            "baz": {"type": "number"},
            "backref": {"$ref": "file2.json#/definitions/nested_back/back"},
            "qux": {"type": "null"},
            "remote_nested": {"$ref": "file2.json#/definitions/nested_remote"}
        }
    },
    "base/file2.json": {
        "definitions": {
            "bar": {"type": "integer"},
            "nested_back": {"back": {"$ref": "file1.json#/definitions/qux"}},
            "nested_remote": {"foo": {"$ref": "#/definitions/mux"}},
            "mux": {"type": "array"},
        }
    },
    "base/reflist.json": {
        "definitions": {
            "foo": {"not": [{"$ref": "#/definitions/baz"}]},
            "baz": {"type": "object"},
        }
    },
}


def get_document(uri: URI):
    return TEST_DATA[uri.root]


@pytest.fixture(scope="module", autouse=True)
def override_loader():
    patcher = patch("json_ref_dict.get_document", get_document)
    mock_loader = patcher.start()
    yield mock_loader
    patcher.stop()


def test_get_no_ref():
    uri = URI.from_string("base/file1.json#/definitions/foo")
    data = resolve_uri(uri)
    assert data == {"type": "string"}


def test_get_local_ref():
    local_ref_uri = URI.from_string("base/file1.json#/definitions/local_ref")
    local_ref = resolve_uri(local_ref_uri)
    assert local_ref == {"type": "number"}


def test_get_remote_ref():
    remote_ref_uri = URI.from_string("base/file1.json#/definitions/remote_ref")
    remote_ref = resolve_uri(remote_ref_uri)
    assert remote_ref == {"type": "integer"}


def test_get_backref():
    backref_uri = URI.from_string("base/file1.json#/definitions/backref")
    backref = resolve_uri(backref_uri)
    assert backref == {"type": "null"}


@pytest.mark.foo
def test_get_nested_remote_ref():
    nested_remote_uri = URI.from_string(
        "base/file1.json#/definitions/remote_nested/foo"
    )
    nested_remote = resolve_uri(nested_remote_uri)
    assert nested_remote == {"type": "array"}


@pytest.fixture(scope="module")
def ref_dict():
    return RefDict(URI.from_string("base/file1.json#/definitions"))


def test_load_dict_no_ref(ref_dict: RefDict):
    assert ref_dict["foo"] == {"type": "string"}


def test_load_dict_local_ref(ref_dict: RefDict):
    assert ref_dict["local_ref"] == {"type": "number"}


def test_load_dict_remote_ref(ref_dict: RefDict):
    assert ref_dict["remote_ref"] == {"type": "integer"}


def test_load_dict_backref(ref_dict: RefDict):
    assert ref_dict["backref"] == {"type": "null"}


def test_load_dict_remote_nested_ref(ref_dict):
    assert ref_dict["remote_nested"]["foo"] == {"type": "array"}


def test_references_propagate_through_arrays():
    ref_dict = RefDict("base/reflist.json#/definitions")
    assert ref_dict["foo"]["not"][0] == {"type": "object"}


def test_direct_reference_retrieval_in_array():
    assert RefDict("base/reflist.json#/definitions/foo/not/0") == {
        "type": "object"
    }

def test_pointer():
    ref_dict = RefDict("base/reflist.json#/")
    pointer = JsonPointer("/definitions/foo/not/0")
    assert pointer.resolve(ref_dict) == {"type": "object"}
