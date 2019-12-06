import pytest

from json_ref_dict import RefDict
from json_ref_dict.exceptions import DocumentParseError


class TestRefDictFileSystemRefs:
    @staticmethod
    @pytest.fixture(scope="module")
    def schema():
        return RefDict("tests/schemas/master.yaml#/definitions")

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
