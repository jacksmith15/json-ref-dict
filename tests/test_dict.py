from typing import Any, Dict, Iterable, Tuple, Union
from unittest.mock import patch

from jsonpointer import JsonPointer
import pytest

from json_ref_dict import resolve_uri, RefDict, RefPointer, URI


TEST_DATA = {
    "base/file1.json": {
        "definitions": {
            "foo": {"type": "string"},
            "remote_ref": {"$ref": "file2.json#/definitions/bar"},
            "local_ref": {"$ref": "#/definitions/baz"},
            "baz": {"type": "number"},
            "backref": {"$ref": "file2.json#/definitions/nested_back/back"},
            "qux": {"type": "null"},
            "remote_nested": {"$ref": "file2.json#/definitions/nested_remote"},
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


def get_document(base_uri: str):
    return TEST_DATA[base_uri]


@pytest.fixture(scope="module", autouse=True)
def override_loader():
    patcher = patch("json_ref_dict.get_document", get_document)
    mock_loader = patcher.start()
    yield mock_loader
    patcher.stop()


class TestResolveURI:
    @staticmethod
    def test_get_no_ref():
        uri = URI.from_string("base/file1.json#/definitions/foo")
        data = resolve_uri(uri)
        assert data == {"type": "string"}

    @staticmethod
    def test_get_local_ref():
        local_ref_uri = URI.from_string(
            "base/file1.json#/definitions/local_ref"
        )
        local_ref = resolve_uri(local_ref_uri)
        assert local_ref == {"type": "number"}

    @staticmethod
    def test_get_remote_ref():
        remote_ref_uri = URI.from_string(
            "base/file1.json#/definitions/remote_ref"
        )
        remote_ref = resolve_uri(remote_ref_uri)
        assert remote_ref == {"type": "integer"}

    @staticmethod
    def test_get_backref():
        backref_uri = URI.from_string("base/file1.json#/definitions/backref")
        backref = resolve_uri(backref_uri)
        assert backref == {"type": "null"}

    @staticmethod
    def test_get_nested_remote_ref():
        nested_remote_uri = URI.from_string(
            "base/file1.json#/definitions/remote_nested/foo"
        )
        nested_remote = resolve_uri(nested_remote_uri)
        assert nested_remote == {"type": "array"}


class TestRefDict:
    @staticmethod
    @pytest.fixture(scope="class")
    def ref_dict():
        return RefDict(URI.from_string("base/file1.json#/definitions"))

    @staticmethod
    def test_load_dict_no_ref(ref_dict: RefDict):
        assert ref_dict["foo"] == {"type": "string"}

    @staticmethod
    def test_load_dict_local_ref(ref_dict: RefDict):
        assert ref_dict["local_ref"] == {"type": "number"}

    @staticmethod
    def test_load_dict_remote_ref(ref_dict: RefDict):
        assert ref_dict["remote_ref"] == {"type": "integer"}

    @staticmethod
    def test_load_dict_backref(ref_dict: RefDict):
        assert ref_dict["backref"] == {"type": "null"}

    @staticmethod
    def test_load_dict_remote_nested_ref(ref_dict):
        assert ref_dict["remote_nested"]["foo"] == {"type": "array"}

    @staticmethod
    def test_references_propagate_through_arrays():
        ref_dict = RefDict("base/reflist.json#/definitions")
        assert ref_dict["foo"]["not"][0] == {"type": "object"}

    @staticmethod
    def test_direct_reference_retrieval_in_array():
        assert RefDict("base/reflist.json#/definitions/foo/not/0") == {
            "type": "object"
        }

    @staticmethod
    def test_json_pointer_on_dict():
        ref_dict = RefDict("base/reflist.json#/")
        pointer = JsonPointer("/definitions/foo/not/0")
        assert pointer.resolve(ref_dict) == {"type": "object"}


class TestRefPointer:
    @staticmethod
    @pytest.fixture(scope="class")
    def uri() -> URI:
        return URI.from_string("base/file1.json#/")

    @staticmethod
    @pytest.fixture(scope="class")
    def document(uri: URI) -> Dict[str, Any]:
        return get_document(uri.root)

    @staticmethod
    @pytest.mark.parametrize("method", ["resolve", "get"])
    @pytest.mark.parametrize(
        "path,expected",
        [
            (("foo",), {"type": "string"}),
            (("remote_ref",), {"type": "integer"}),
            (("local_ref",), {"type": "number"}),
            (("backref",), {"type": "null"}),
            (("remote_nested", "foo"), {"type": "array"}),
        ],
    )
    def test_ref_pointer_resolve(
        uri: URI,
        document: Dict[str, Any],
        method: str,
        path: Iterable[str],
        expected: Any,
    ):
        pointer = RefPointer(uri.get("definitions", *path))
        assert getattr(pointer, method)(document) == expected

    @staticmethod
    @pytest.mark.parametrize(
        "path,expected",
        [
            (("foo",), "/definitions/foo"),
            (("remote_ref",), "/definitions/remote_ref"),
            (("local_ref",), "/definitions/local_ref"),
            (("backref",), "/definitions/backref"),
            (("remote_nested", "foo"), "/definitions/remote_nested/foo"),
        ],
    )
    def test_re_pointer_path(uri: URI, path: Iterable[str], expected: str):
        pointer = RefPointer(uri.get("definitions", *path))
        assert pointer.path == expected

    @staticmethod
    @pytest.mark.parametrize(
        "path",
        [
            ("foo",),
            ("remote_ref",),
            ("local_ref",),
            ("backref",),
            ("remote_nested", "foo"),
        ],
    )
    def test_set_fails(uri: URI, document: Dict[str, Any], path: Iterable[str]):
        pointer = RefPointer(uri.get("definitions", *path))
        with pytest.raises(NotImplementedError):
            pointer.set(document, "foo")

    @staticmethod
    @pytest.mark.parametrize(
        "path,expected",
        [
            (("foo", "type"), ({"type": "string"}, "type")),
            (("remote_ref", "type"), ({"type": "integer"}, "type")),
            (("local_ref", "type"), ({"type": "number"}, "type")),
            (("backref", "type"), ({"type": "null"}, "type")),
            (("remote_nested", "foo", "type"), ({"type": "array"}, "type")),
        ],
    )
    def test_to_last(
        uri: URI,
        document: Dict[str, Any],
        path: Iterable[str],
        expected: Tuple[Any, Union[str, int]],
    ):
        pointer = RefPointer(uri.get("definitions", *path))
        assert pointer.to_last(document) == expected
