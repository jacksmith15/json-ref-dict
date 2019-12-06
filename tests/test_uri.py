import pytest

from json_ref_dict import URI
from json_ref_dict.exceptions import ReferenceParseError


@pytest.mark.parametrize(
    "reference", ["foobar", "foobar#", "foobar#definitions", "#definitions"]
)
def test_from_string_fails_for_bad_references(reference: str):
    with pytest.raises(ReferenceParseError):
        _ = URI.from_string(reference)


def test_relative_raises_type_error_if_passed_bad_reference():
    with pytest.raises(TypeError):
        _ = URI(uri_base="foo", uri_name="bar", pointer="/foo/bar").relative({})
