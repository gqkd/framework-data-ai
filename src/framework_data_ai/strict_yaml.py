"""YAML that refuses a key written twice in one mapping.

`yaml.safe_load` folds two rows with one key into the last of them without a word, which is
how two branches that each added `OD-042` to `entries:` would become one entry once merged.
Whatever has to tell "both keys are there" from "one of them was lost" reads with this. One
loader for the framework: the memory contracts were the first to need it.
"""
from __future__ import annotations

import yaml


class DuplicateKey(ValueError):
    """A key written twice in one mapping."""


class _Unique(yaml.SafeLoader):
    pass


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise DuplicateKey(f"`{key}` twice in one mapping, line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_Unique.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load(text: str | bytes):
    """Like `yaml.safe_load`, and `DuplicateKey` for a key written twice in one mapping."""
    return yaml.load(text, Loader=_Unique)
