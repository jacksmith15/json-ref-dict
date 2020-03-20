from os import path
import re
from typing import NamedTuple
from urllib.parse import urlparse

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
        if "#" not in string:
            string += "#/"
        if string.endswith("#"):
            string += "/"
        match = re.match(JSON_REF_REGEX, string)
        if not match:
            raise ReferenceParseError(
                f"Couldn't parse '{string}' as a valid reference. "
                "References must be of the format "
                "{base_uri}#{json_pointer}, where 'json_pointer' "
                "begins with '/'"
            )
        return URI(**match.groupdict())

    @property
    def root(self):
        """String representation excluding the JSON pointer."""
        return path.join(*filter(None, [self.uri_base, self.uri_name]))

    def _get_relative(self, reference: str) -> "URI":
        """Get a new URI relative to the current root."""
        if not isinstance(reference, str):
            raise TypeError(f"Got invalid value for '$ref': {reference}.")
        if not reference.split("#")[0]:  # Local reference.
            reference = reference.split("#")[1] or "/"
            return URI(self.uri_base, self.uri_name, reference)
        # Remote reference.
        return self.from_string(
            path.join(*filter(None, [self.uri_base, reference]))
        )

    def relative(self, reference: str) -> "URI":
        """Get a new URI relative to the current root.

        :raises ReferenceParseError: if relative reference is equal
          to the current reference.
        :return: The URI of the reference relative to the current URI.
        """
        if is_absolute(reference):
            relative_uri = URI.from_string(reference)
        else:
            relative_uri = self._get_relative(reference)
        if relative_uri == self:
            raise ReferenceParseError(
                f"Reference: '{reference}' from context '{self}' is "
                "self-referential. Cannot resolve."
            )
        return relative_uri

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
        return self.root + f"#{self.pointer}"


def is_absolute(ref: str) -> bool:
    """Check if URI is absolute based on scheme."""
    parsed = urlparse(ref)
    if parsed.scheme:
        return True
    return False


def parse_segment(segment: str) -> str:
    """Parse a pointer segment.

    Individual segments need to replace special chars, as per RFC-6901:
    https://tools.ietf.org/html/rfc6901
    """
    return segment.replace("~", "~0").replace("/", "~1")
