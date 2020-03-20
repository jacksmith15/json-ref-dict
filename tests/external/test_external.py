"""Regression tests for external documents found to fail."""
import pytest

from json_ref_dict import RefDict


@pytest.mark.parametrize(
    "uri", ["http://json.schemastore.org/cryproj.52.schema"]
)
def test_external_document_loads_correctly(uri: str):
    assert RefDict(uri)
