from collections import UserDict, UserList
from typing import Any, Union

from json_ref_dict.ref_pointer import resolve_uri
from json_ref_dict.uri import parse_segment, URI


class RefDict(UserDict):  # pylint: disable=too-many-ancestors
    """Dictionary for abstracting ref resolution in JSONSchemas.

    Accepts a base URI as its argument, and subsequently can be
    accessed as any other dictionary. Behaviour propagates to
    nested items.
    """

    def __init__(self, uri: Union[str, URI], *args, **kwargs):
        """On instantiation, retrieve the data from the URI."""
        self.uri = URI.from_string(uri) if isinstance(uri, str) else uri
        value = resolve_uri(self.uri)
        if not isinstance(value, dict):
            raise TypeError(
                f"The value at '{uri}' is not an object. Got '{value}'."
            )
        super().__init__(**value)

    def __getitem__(self, key: str):
        """Propagate ref resolution behaviour to nested objects."""
        item = super().__getitem__(key)
        uri = self.uri.get(parse_segment(key))
        return propagate(uri, item)

    @staticmethod
    def from_uri(
        uri: Union[str, URI]
    ) -> Union["RefDict", "RefList", None, bool, str, int, float]:
        """Convert URI to corresponding data type.

        Looks ahead at the raw value, and then returns a RefDict, RefList, or
        other value.
        """
        uri = URI.from_string(uri) if isinstance(uri, str) else uri
        value = resolve_uri(uri)
        if isinstance(value, dict):
            return RefDict(uri)
        if isinstance(value, list):
            return RefList(uri)
        return value


class RefList(UserList):  # pylint: disable=too-many-ancestors
    """List for abstracting ref resolution in JSONSchemas.

    Accepts a base URI as its argument, and subsequently can be
    accessed as any other list. Behaviour propagates to
    nested items.
    """

    def __init__(self, uri: Union[str, URI], *args, **kwargs):
        """On instantiation, retrieve the data from the URI."""
        self.uri = URI.from_string(uri) if isinstance(uri, str) else uri
        value = resolve_uri(self.uri)
        if not isinstance(value, list):
            raise TypeError(
                f"The value at '{uri}' is not an array. Got '{value}'."
            )
        super().__init__(value)

    def __getitem__(self, index: Union[int, slice]):
        """Propagate ref resolution behaviour to nested objects."""
        item = super().__getitem__(index)
        uri = self.uri.get(str(index))
        return propagate(uri, item)


def propagate(uri: URI, value: Any):
    """Ref resolution and propagation of behaviours on __getitem__."""
    if isinstance(value, dict):
        if "$ref" in value and isinstance(value["$ref"], str):
            return RefDict.from_uri(uri.relative(value["$ref"]))
        return RefDict(uri)
    if isinstance(value, list):
        return RefList(uri)
    return value
