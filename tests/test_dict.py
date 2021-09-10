from typing import Any, Dict, Iterable, Tuple, Union
from unittest.mock import patch
from jsonpointer import JsonPointer, JsonPointerException
import pytest

from json_ref_dict import resolve_uri, RefDict, RefPointer, URI
from json_ref_dict.ref_dict import RefList
from json_ref_dict.loader import get_document, loader

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
    "base/nonref.json": {"definitions": {"$ref": {"type": "string"}}},
    "base/with-spaces.json": {
        "top": {
            "with spaces": {"foo": "bar"},
            "ref to spaces": {"$ref": "#/top/with spaces"},
        }
    },
    "base/with-spaces-encoded.json": {
        "top": {
            "with spaces": {"foo": "bar"},
            "ref to spaces": {"$ref": "#/top/with%20spaces"},
        }
    },
    "base/with-newline.json": {
        "top": {
            "with\nnewline": {"foo": "bar"},
            "ref\nto\nnewline": {"$ref": "#/top/with\nnewline"},
        }
    },
    "base/with-newline-encoded.json": {
        "top": {
            "with\nnewline": {"foo": "bar"},
            "ref\nto\nnewline": {"$ref": "#/top/with%0Anewline"},
        }
    },
    "base/ref-to-primitive.json": {
        "top": {
            "primitive": "foo",
            "ref_to_primitive": {"$ref": "#/top/primitive"},
        }
    },
    "base/with-escaped-chars.json": {
        "tilda~field": {"type": "integer"},
        "slash/field": {"type": "integer"},
        "percent%field": {"type": "integer"},
        "properties": {
            "tilda": {"$ref": "#/tilda~0field"},
            "slash": {"$ref": "#/slash~1field"},
            "percent": {"$ref": "#/percent%25field"},
        },
    },
    "base/from-uri.json": {
        "refs": {
            "to_array": {"$ref": "#/array"},
            "to_object": {"$ref": "#/object"},
            "to_primitive": {"$ref": "#/primitive"},
        },
        "array": [1, 2, 3],
        "object": {"foo": "bar"},
        "primitive": 1,
    },
}


@pytest.fixture(scope="module", autouse=True)
def override_loader():
    @loader.register
    def _get_document(base_uri: str):
        return TEST_DATA[base_uri]

    try:
        yield
    finally:
        loader.clear()


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
    def test_get_remote_ref_cache_clear_reloads():
        remote_ref_uri = URI.from_string(
            "base/file1.json#/definitions/remote_ref"
        )
        resolve_uri.cache_clear()
        with patch(f"{resolve_uri.__module__}.get_document") as mock_doc:
            mock_doc.side_effect = get_document
            _ = [resolve_uri(remote_ref_uri) for _ in range(3)]
            assert mock_doc.call_count == 2  # file1 and file2 loaded
            resolve_uri.cache_clear()
            remote_ref = resolve_uri(remote_ref_uri)
            assert mock_doc.call_count == 4
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

    @staticmethod
    def test_get_non_reference():
        non_ref_uri = URI.from_string("base/nonref.json#/definitions")
        non_ref = resolve_uri(non_ref_uri)
        assert non_ref["$ref"] == {"type": "string"}

    @staticmethod
    @pytest.mark.parametrize(
        "reference",
        [
            "base/with-spaces.json#/top/with spaces",
            "base/with-spaces.json#/top/with%20spaces",
        ],
    )
    def test_get_uri_with_spaces(reference: str):
        uri = URI.from_string(reference)
        result = resolve_uri(uri)
        assert result == {"foo": "bar"}

    @staticmethod
    @pytest.mark.parametrize(
        "base", ["base/with-spaces.json", "base/with-spaces-encoded.json"]
    )
    def test_get_ref_with_spaces(base: str):
        uri = URI.from_string(f"{base}#/top/ref to spaces/foo")
        result = resolve_uri(uri)
        assert result == "bar"

    @staticmethod
    @pytest.mark.parametrize(
        "reference",
        [
            "base/with-newline.json#/top/with\nnewline",
            "base/with-newline.json#/top/with%0Anewline",
        ],
    )
    def test_get_uri_with_newline(reference: str):
        uri = URI.from_string(reference)
        result = resolve_uri(uri)
        assert result == {"foo": "bar"}

    @staticmethod
    @pytest.mark.parametrize(
        "base", ["base/with-newline.json", "base/with-newline-encoded.json"]
    )
    def test_get_ref_with_newline(base: str):
        uri = URI.from_string(f"{base}#/top/ref\nto\nnewline/foo")
        result = resolve_uri(uri)
        assert result == "bar"

    @staticmethod
    @pytest.mark.parametrize("field", ["tilda", "slash", "percent"])
    def test_get_ref_with_escaped_chars(field: str):
        uri = URI.from_string(
            f"base/with-escaped-chars.json#/properties/{field}"
        )
        result = resolve_uri(uri)
        assert result == {"type": "integer"}


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
    def test_get_non_ref_ref_key():
        assert RefDict("base/nonref.json#/definitions")["$ref"] == {
            "type": "string"
        }

    @staticmethod
    @pytest.mark.parametrize(
        "reference",
        [
            "base/reflist.json#/definitions/foo/not",
            "base/file1.json#/definitions/foo/type",
            "base/file1.json#/definitions/backref/type",
        ],
    )
    def test_ref_dict_raises_when_target_is_not_object(reference: str):
        with pytest.raises(TypeError):
            _ = RefDict(reference)

    @staticmethod
    @pytest.mark.parametrize(
        "reference",
        [
            "base/reflist.json#/definitions/foo/not/0",
            "base/file1.json#/definitions/foo",
            "base/file1.json#/definitions/backref/type",
        ],
    )
    def test_ref_list_raises_when_target_is_not_array(reference: str):
        with pytest.raises(TypeError):
            _ = RefList(reference)

    @staticmethod
    def test_json_pointer_on_dict():
        ref_dict = RefDict("base/reflist.json#/")
        pointer = JsonPointer("/definitions/foo/not/0")
        assert pointer.resolve(ref_dict) == {"type": "object"}

    @staticmethod
    def test_dict_with_ref_to_primitive():
        ref_dict = RefDict("base/ref-to-primitive.json#/")
        assert ref_dict["top"]["primitive"] == "foo"
        assert ref_dict["top"]["ref_to_primitive"] == "foo"

    @staticmethod
    def test_from_uri_object():
        ref_dict = RefDict.from_uri("base/ref-to-primitive.json#/")
        assert ref_dict == RefDict("base/ref-to-primitive.json#/")


class TestFromURI:
    @staticmethod
    def test_from_uri_list():
        ref_list = RefDict.from_uri("base/from-uri.json#/array")
        assert ref_list == [1, 2, 3]

    @staticmethod
    def test_from_uri_object():
        ref_dict = RefDict.from_uri("base/from-uri.json#/object")
        assert ref_dict == {"foo": "bar"}

    @staticmethod
    def test_from_uri_primitive():
        ref_primitive = RefDict.from_uri("base/from-uri.json#/primitive")
        assert ref_primitive == 1

    @staticmethod
    def test_from_uri_immediate_ref_list():
        ref_list = RefDict.from_uri("base/from-uri.json#/refs/to_array")
        assert ref_list == [1, 2, 3]

    @staticmethod
    def test_from_uri_immediate_ref_object():
        ref_object = RefDict.from_uri("base/from-uri.json#/refs/to_object")
        assert ref_object == {"foo": "bar"}

    @staticmethod
    def test_from_uri_immediate_ref_primitive():
        ref_primitive = RefDict.from_uri(
            "base/from-uri.json#/refs/to_primitive"
        )
        assert ref_primitive == 1


class TestRefPointer:
    @staticmethod
    @pytest.fixture(scope="class")
    def uri() -> URI:
        return URI.from_string("base/file1.json#/")

    @staticmethod
    @pytest.fixture(scope="class")
    def document(uri: URI) -> Dict[str, Any]:
        return loader(uri.root)

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

    @staticmethod
    def test_ref_pointer_raises_on_no_match(uri: URI, document: Dict[str, Any]):
        with pytest.raises(JsonPointerException):
            _ = RefPointer(uri.get("nonexistent")).resolve(document)

    @staticmethod
    def test_ref_pointer_returns_default_if_no_match(
        uri: URI, document: Dict[str, Any]
    ):
        default = "default"
        assert RefPointer(uri.get("nonexistent")).resolve(
            document, default=default
        )

    @staticmethod
    def test_ref_pointer_returns_non_dict_values(
        uri: URI, document: Dict[str, Any]
    ):
        uri = uri.get("definitions").get("foo").get("type")
        assert RefPointer(uri).resolve(document) == "string"

    @staticmethod
    def test_ref_to_primitive():
        uri = URI.from_string(
            "base/ref-to-primitive.json#/top/ref_to_primitive"
        )
        document = loader(uri.root)
        assert RefPointer(uri).resolve(document) == "foo"
