[![Build Status](https://travis-ci.com/jacksmith15/json-ref-dict.svg?branch=master)](https://travis-ci.com/jacksmith15/json-ref-dict)
# JSONSchema Ref Dict
Python dict-like object which abstracts resolution of JSONSchema references.

```python
from json_ref_dict import RefDict

schema = RefDict("https://json-schema.org/draft-07/schema#/")
```

Nested items containing `"$ref"` will be resolved lazily when accessed,
meaning the dictionary can be treating as a single, continuous (and
possibly infinite) document.

Remote references are supported, and will be resolved relative to the current
document.

If no scheme is provided, it is assumed that the document is present on the
local filesystem (see [Example](#example) below).

If [PyYAML](https://github.com/yaml/pyyaml) is installed, then loading of YAML documents will be supported, otherwise only JSON documents may be loaded.

## Example
Given the following related schemas:
#### _master.yaml_
```yaml
definitions:
  foo:
    type: string
  local_ref:
    $ref: '#/definitions/foo'
  remote_ref:
    $ref: 'other.yaml#/definitions/bar'
  backref:
    $ref: 'other.yaml#/definitions/baz'
```

#### _other.yaml_
```yaml
definitions:
  bar:
    type: integer
  baz:
    $ref: 'master.yaml#/definitions/foo'
```

We can parse these as a single object as follows:
```python
from json_ref_dict import RefDict

schema = RefDict("master.yaml#/definitions")
print(schema)
>>> {'foo': {'type': 'string'}, 'local_ref': {'$ref': '#/definitions/foo'}, 'remote_ref': {'$ref': 'other.yaml#/definitions/bar'}, 'backref': {'$ref': 'other.yaml#/definitions/baz'}}

print(schema["local_ref"])
>>> {'type': 'string'}

print(schema["remote_ref"])
>>> {'type': 'integer'}

print(schema["backref"])
>>> {'type': 'string'}
```

## Materializing documents
If you don't want the lazy behaviour, and want to get all of the IO out of the way up front, then you can "materialize" the dictionary:
```python
from json_ref_dict import materialize, RefDict

schema = materialize(RefDict("https://json-schema.org/draft-04/schema#/"))
assert isinstance(schema, dict)
```

A materialized `RefDict` is just a regular dict, containing a document with all references resolved. This is useful if, for example, you want to cache/persist the entire schema. Be aware that if there are cyclical references in the schema, these will be present on the materialized dictionary.

The `materialize` helper also supports some basic transformation options, as performing global transformations on infinite documents is non-trivial:

- `include_keys` - an iterable of keys to include in the materialized document.
- `exclude_keys` - an iterable of keys to exclude from the materialized document.
- `value_map` - an operation to apply to the values of the document (not lists or dictionaries).

# Requirements
This package is currently tested for Python 3.6.

# Installation
This project may be installed using [pip](https://pip.pypa.io/en/stable/):
```
pip install json-ref-dict
```

# Development
1. Clone the repository: `git clone git@github.com:jacksmith15/json-ref-dict.git && cd json-ref-dict`
2. Install the requirements: `pip install -r requirements.txt -r requirements-test.txt`
3. Run `pre-commit install`
4. Run the tests: `bash run_test.sh -c -a`

This project uses the following QA tools:
- [PyTest](https://docs.pytest.org/en/latest/) - for running unit tests.
- [PyLint](https://www.pylint.org/) - for enforcing code style.
- [MyPy](http://mypy-lang.org/) - for static type checking.
- [Travis CI](https://travis-ci.org/) - for continuous integration.
- [Black](https://black.readthedocs.io/en/stable/) - for uniform code formatting.

# License
This project is distributed under the MIT license.
