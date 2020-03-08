from functools import lru_cache
import json
from os import getcwd, path
from typing import Any, Callable, Dict, IO
from urllib.parse import urlparse
from urllib.request import urlopen

from json_ref_dict.exceptions import DocumentParseError


CONTENT_LOADER: Callable[[IO], Dict]

try:
    import yaml

    CONTENT_LOADER = yaml.safe_load
except ImportError:  # pragma: no cover
    CONTENT_LOADER = json.load  # pragma: no cover


@lru_cache(maxsize=None)
def get_document(base_uri: str):
    """Load a document based on URI root."""
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
        prefix = "" if base_uri.startswith("/") else getcwd()
        base_uri = "file://" + path.join(prefix, base_uri)
    if base_uri.endswith(".json"):
        loader: Callable = json.load
    else:
        loader = CONTENT_LOADER
    with urlopen(base_uri) as conn:
        content = loader(conn)
    return content
