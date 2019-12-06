from functools import lru_cache
from os import getcwd, path
from typing import Any, Callable, Dict, IO
from urllib.parse import urlparse
from urllib.request import urlopen

from json_ref_dict.exceptions import DocumentParseError


CONTENT_LOADER: Callable[[IO], Dict]

try:
    import yaml

    CONTENT_LOADER = yaml.safe_load
except ImportError:
    import json

    CONTENT_LOADER = json.load


@lru_cache(maxsize=None)
def get_document(base_uri: str):
    """Load a document based on URI root.

    Currently assumes the URI is a filesystem URI.
    """
    try:
        return _read_document_content(base_uri)
    except Exception as exc:
        raise DocumentParseError(f"Failed to load uri '{base_uri}'.") from exc


def _read_document_content(base_uri: str) -> Dict[str, Any]:
    """Resolve document content from the base URI.

    If the URI has no scheme, assume local filesystem loading, appending
    the current working directory if the path is not absolute.

    Defers to `urllib` and may raise any exceptions from
    `urllib.request.urlopen`.
    :return: Raw content found at the URI.
    """
    url = urlparse(base_uri)
    if not url.scheme:
        prefix = "file://" + ("/" if base_uri.startswith("/") else getcwd())
        base_uri = path.join(prefix, base_uri)
    with urlopen(base_uri) as conn:
        content = CONTENT_LOADER(conn)
    return content
