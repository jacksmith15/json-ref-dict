from json_ref_dict import materialize, RefDict


def test_can_get_json_schema_ref():
    assert RefDict("https://json-schema.org/draft-07/schema#/")


def test_can_materialize_json_schema_ref():
    schema = materialize(RefDict("https://json-schema.org/draft-07/schema#/"))
    assert isinstance(schema, dict)
