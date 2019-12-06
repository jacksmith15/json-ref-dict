from os import path
import re
from typing import NamedTuple


from json_ref_dict.exceptions import ReferenceParseError


JSON_REF_REGEX = r"^((?P<uri_base>.*)\/)?(?P<uri_name>.*)#(?P<pointer>\/.*)$"


class URI(NamedTuple):
    """URI for a schema or subschema."""

    uri_base: str
    uri_name: str
    pointer: str

    @classmethod
    def from_string(cls, string: str) -> "URI":
        """Contruct from string."""
        match = re.match(JSON_REF_REGEX, string)
        if not match:
            raise ReferenceParseError(
                f"Couldn't parse '{string}' as a valid reference."
            )
        return URI(**match.groupdict())

    @property
    def root(self):
        """String representation excluding the JSON pointer."""
        return path.join(self.uri_base, self.uri_name)

    def relative(self, reference: str) -> "URI":
        """Get a new URI relative to the current root."""
        if not isinstance(reference, str):
            raise ReferenceParseError(
                f"Got invalid value for '$ref': {reference}."
            )
        if not reference.split("#")[0]:  # Local reference.
            return URI(self.uri_base, self.uri_name, reference.split("#")[1])
        # Remote reference.
        return self.from_string(path.join(self.uri_base, reference))

    def get(self, *pointer_segments: str) -> "URI":
        """Get a new URI representing a member of the current URI."""
        return self.__class__(
            uri_base=self.uri_base,
            uri_name=self.uri_name,
            pointer=path.join(self.pointer, *pointer_segments),
        )

    def back(self) -> "URI":
        """Pop a segment from the pointer."""
        segments = self.pointer.split("/")
        pointer = path.join("/", *segments[:-1])
        return self.__class__(
            uri_base=self.uri_base, uri_name=self.uri_name, pointer=pointer
        )

    def __repr__(self) -> str:
        """String representation of the URI."""
        return path.join(self.uri_base, self.uri_name) + f"#{self.pointer}"