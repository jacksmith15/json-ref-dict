import pathlib
import posixpath
from os import getcwd

import pytest

from json_ref_dict import RefDict
from json_ref_dict.loader import loader
from json_ref_dict.exceptions import DocumentParseError, ReferenceParseError


PINNED_FILE_URL = (
    "https://raw.githubusercontent.com/jacksmith15/json-ref-dict/091af2"
    "c19989a95449df587b62abea89aeb83676/tests/schemas/master.yaml"
)


def test_loader_registration(request):
    """Tests the loaders iterable management
    """
    request.addfinalizer(loader.clear)

    assert not list(loader)

    # pylint:disable=unused-argument
    @loader.register
    def useless(baseuri):
        return ...

    assert list(loader) == [useless]
    loader.unregister(useless)
    assert list(loader) == []

    with pytest.raises(ValueError) as exc:
        loader.unregister(useless)
    assert str(exc.value) == f"{useless} is not a known loader."

    loader.register(useless)
    with pytest.raises(ValueError) as exc:
        loader.register(useless)
    assert str(exc.value) == f"{useless} is already a known loader."

    loader.clear()
    assert list(loader) == []


def test_loader_registration_chain(request):
    """Tests LIFO registration
    """
    request.addfinalizer(loader.clear)

    @loader.register
    def no_remote(baseuri):
        if baseuri.startswith("http://") or baseuri.startswith("https://"):
            return ...
        return {"foo": "bar"}

    @loader.register
    def file_loader(baseuri):
        if baseuri.startswith("file://"):
            return {"bar": "qux"}
        return ...

    assert list(loader) == [file_loader, no_remote]

    schema = loader("file://myfile.json")
    assert schema == {"bar": "qux"}

    schema = loader(PINNED_FILE_URL)
    assert dict(schema) == {
        "definitions": {
            "backref": {"$ref": "other.yaml#/definitions/baz"},
            "foo": {"type": "string"},
            "local_ref": {"$ref": "#/definitions/foo"},
            "remote_ref": {"$ref": "other.yaml#/definitions/bar"},
        }
    }

    schema = loader("not https")
    assert schema == {"foo": "bar"}


class TestRefDictIORefs:
    @staticmethod
    @pytest.fixture(
        scope="class",
        params=[
            # relative filepath
            "tests/schemas/master.yaml#/definitions",
            # absolute filepath
            posixpath.join(getcwd(), "tests/schemas/master.yaml#/definitions"),
            # explicit file scheme
            (
                pathlib.Path(
                    posixpath.join(getcwd(), "tests/schemas/master.yaml")
                ).as_uri()
                + "#/definitions"
            ),
            # https URI
            PINNED_FILE_URL + "#/definitions",
        ],
    )
    def schema(request):
        return RefDict(request.param)

    @staticmethod
    def test_schema_loads(schema):
        assert str(schema) == str(
            {
                "foo": {"type": "string"},
                "local_ref": {"$ref": "#/definitions/foo"},
                "remote_ref": {"$ref": "other.yaml#/definitions/bar"},
                "backref": {"$ref": "other.yaml#/definitions/baz"},
            }
        )

    @staticmethod
    def test_local_ref(schema):
        assert schema["local_ref"] == {"type": "string"}

    @staticmethod
    def test_remote_ref(schema):
        assert schema["remote_ref"] == {"type": "integer"}

    @staticmethod
    def test_backref(schema):
        assert schema["backref"] == {"type": "string"}

    @staticmethod
    def test_casting_to_dict_dereferences_all(schema):
        assert dict(schema) == {
            "foo": {"type": "string"},
            "local_ref": {"type": "string"},
            "remote_ref": {"type": "integer"},
            "backref": {"type": "string"},
        }

    @staticmethod
    def test_loading_unknown_file_raises_document_parse_error():
        with pytest.raises(DocumentParseError):
            _ = RefDict("tests/schemas/nonexistent.yaml#/definitions")

    @staticmethod
    def test_loading_a_json_file_with_tabs_falls_back_to_json_loader():
        """YAML is _mostly_ compatible with JSON.

        However, JSON allows tabs between tokens, whilst YAML does not.
        """
        value = RefDict("tests/schemas/with-tabs.json")
        assert dict(value) == {"some": {"json": ["with", "tabs"]}}


def test_immediately_circular_reference_fails():
    with pytest.raises(ReferenceParseError):
        _ = RefDict("tests/schemas/bad-circular.yaml#/definitions/foo")


def test_immediate_references_is_detected():
    value = RefDict.from_uri("tests/schemas/immediate-ref.json")
    assert value == {"type": "integer"}


def test_immediate_references_can_be_bypassed():
    value = RefDict.from_uri("tests/schemas/immediate-ref.json#/type")
    assert value == "integer"
