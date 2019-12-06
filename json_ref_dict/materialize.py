from os import path
from typing import Any, Dict, NamedTuple, Set, Tuple, TypeVar

from jsonpointer import JsonPointer

from json_ref_dict.uri import URI
from json_ref_dict.ref_dict import RefDict, RefList


RefContainer = TypeVar("RefContainer", RefDict, RefList)


def next_path(current_path: str):
    def _wrap(segment: str):
        return path.join(current_path, segment)

    return _wrap


class RepeatCache(NamedTuple):

    source: JsonPointer
    repeats: Set[JsonPointer]

    def __hash__(self):
        return self.source.__hash__()


def materialize(item: RefContainer):
    repeats: Dict[URI, RepeatCache] = {}
    materialized = _materialize_recursive(repeats, "/", item)
    for duplicate in repeats.values():
        if duplicate.source.path == "/":
            value = materialized
        else:
            value = duplicate.source.resolve(materialized)
        for repeat in duplicate.repeats:
            repeat.set(materialized, value)
    return materialized


def _materialize_recursive(
    repeats: Dict[URI, RepeatCache], pointer: str, item: Any
) -> Any:
    if not isinstance(item, (RefDict, RefList)):
        return item
    if item.uri in repeats:
        repeats[item.uri][1].add(JsonPointer(pointer))
        return None
    repeats[item.uri] = RepeatCache(source=JsonPointer(pointer), repeats=set())
    recur = lambda seg, data: _materialize_recursive(
        repeats, next_path(pointer)(seg), data
    )
    if isinstance(item, RefList):
        return [recur(idx, subitem) for idx, subitem in enumerate(item)]
    return {key: recur(key, value) for key, value in item.items()}
