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


@pytest.mark.foo
class TestRefDictHTTPefs:
    @staticmethod
    @pytest.fixture(scope="module")
    def schema():
        # Permalink to file url on Github.
        file_url = (
            "https://raw.githubusercontent.com/jacksmith15/json-ref-dict/091af2"
            "c19989a95449df587b62abea89aeb83676/tests/schemas/master.yaml"
        )
        return RefDict(f"{file_url}#/definitions")

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
