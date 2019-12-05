from unittest.mock import patch

import pytest

from json_ref_dict import _get_uri, RefDict, URI


TEST_DATA = {
    "base/file1.json": {
        "definitions": {
            "foo": {"type": "string"},
            "remote_ref": {"$ref": "file2.json#/definitions/bar"},
            "local_ref": {"$ref": "#/definitions/baz"},
            "baz": {"type": "number"},
            "backref": {"$ref": "file2.json#/definitions/nested/back"},
            "qux": {"type": "null"},
        }
    },
    "base/file2.json": {
        "definitions": {
            "bar": {"type": "integer"},
            "nested": {"back": {"$ref": "file1.json#/definitions/qux"}},
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
    data = _get_uri(uri)
    assert data == {"type": "string"}


def test_get_local_ref():
    local_ref_uri = URI.from_string("base/file1.json#/definitions/local_ref")
    local_ref = _get_uri(local_ref_uri)
    assert local_ref == {"type": "number"}


def test_get_remote_ref():
    remote_ref_uri = URI.from_string("base/file1.json#/definitions/remote_ref")
    remote_ref = _get_uri(remote_ref_uri)
    assert remote_ref == {"type": "integer"}


def test_get_backref():
    backref_uri = URI.from_string("base/file1.json#/definitions/backref")
    backref = _get_uri(backref_uri)
    assert backref == {"type": "null"}


@pytest.fixture(scope="module")
def ref_dict():
    return RefDict(URI.from_string("base/file1.json#/definitions"))


def test_get_load_dict_no_ref(ref_dict: RefDict):
    assert ref_dict["foo"] == {"type": "string"}


def test_get_load_dict_local_ref(ref_dict: RefDict):
    assert ref_dict["local_ref"] == {"type": "number"}


def test_get_load_dict_remote_ref(ref_dict: RefDict):
    assert ref_dict["remote_ref"] == {"type": "integer"}


def test_get_load_dict_backref(ref_dict: RefDict):
    assert ref_dict["backref"] == {"type": "null"}


def test_references_propagate_through_arrays():
    ref_dict = RefDict("base/reflist.json#/definitions")
    assert ref_dict["foo"]["not"][0] == {"type": "object"}


def test_direct_reference_retrieval_in_array():
    assert RefDict("base/reflist.json#/definitions/foo/not/0") == {
        "type": "object"
    }
