from os import getcwd, path

import pytest

from json_ref_dict import RefDict
from json_ref_dict.exceptions import DocumentParseError, ReferenceParseError


PINNED_FILE_URL = (
    "https://raw.githubusercontent.com/jacksmith15/json-ref-dict/091af2"
    "c19989a95449df587b62abea89aeb83676/tests/schemas/master.yaml"
)


class TestRefDictFileSystemRefs:
    @staticmethod
    @pytest.fixture(
        scope="class",
        params=[
            # relative filepath
            "tests/schemas/master.yaml#/definitions",
            # absolute filepath
            path.join(getcwd(), "tests/schemas/master.yaml#/definitions"),
            # explicit file scheme
            (
                "file://"
                + path.join(getcwd(), "tests/schemas/master.yaml#/definitions")
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


def test_immediately_circular_reference_fails():
    with pytest.raises(ReferenceParseError):
        _ = RefDict("tests/schemas/bad-circular.yaml#/definitions/foo")
