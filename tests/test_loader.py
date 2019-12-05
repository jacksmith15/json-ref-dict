import pytest

from json_ref_dict import RefDict


@pytest.fixture(scope="module")
def schema():
    return RefDict("tests/schemas/master.yaml#/definitions")


def test_schema_loads(schema):
    assert str(schema) == str({
        "foo": {"type": "string"},
        "local_ref": {"$ref": "#/definitions/foo"},
        "remote_ref": {"$ref": "other.yaml#/definitions/bar"},
        "backref": {"$ref": "other.yaml#/definitions/baz"},
    })


def test_local_ref(schema):
    assert schema["local_ref"] == {"type": "string"}


def test_remote_ref(schema):
    assert schema["remote_ref"] == {"type": "integer"}


def test_backref(schema):
    assert schema["backref"] == {"type": "string"}


def test_casting_to_dict_dereferences_all(schema):
    assert dict(schema) == {
        "foo": {"type": "string"},
        "local_ref": {"type": "string"},
        "remote_ref": {"type": "integer"},
        "backref": {"type": "string"},
    }
