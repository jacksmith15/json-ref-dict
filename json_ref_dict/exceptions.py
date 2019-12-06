class JSONRefParseError(Exception):
    """Base exception for failures when parsing."""


class DocumentParseError(JSONRefParseError):
    """Failed to parse a document."""


class ReferenceParseError(JSONRefParseError):
    """Failed to parse a reference."""
