"""Regression tests for external documents found to fail."""
import pytest

from json_ref_dict import materialize, RefDict


@pytest.mark.parametrize(
    "uri",
    [
        "http://json.schemastore.org/cryproj.52.schema",
        "http://json.schemastore.org/swagger-2.0",
    ],
)
def test_external_document_loads_correctly(uri: str):
    dictionary = materialize(RefDict(uri))
    assert dictionary
