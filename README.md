[![Build Status](https://travis-ci.com/jacksmith15/json-ref-dict.svg?branch=master)](https://travis-ci.com/jacksmith15/json-ref-dict)
# JSONSchema Ref Dict
Python dict-like object which abstracts resolution of JSONSchema references.

Supports file-system reference resolution, but support for other schemes is likely to be added.

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

If you don't care about lazy-loading, you can just cast the object to a `dict` to resolve all references:
```python
print(dict(schema))
>>> {'foo': {'type': 'string'}, 'local_ref': {'type': 'string'}, 'remote_ref': {'type': 'integer'}, 'backref': {'type': 'string'}}
```

# Requirements
This package is currently tested for Python 3.6.

# Installation
This project is not currently packaged and so must be installed manually.

Clone the project with the following command:
```
git clone https://github.com/jacksmith15/json-ref-dict.git
```

Package requirements may be installed via `pip install -r requirements.txt`. Use of a [virtualenv](https://virtualenv.pypa.io/) is recommended.

# Development
1. Clone the repository: `git clone git@github.com:jacksmith15/json-ref-dict.git && cd json-ref-dict`
2. Install the requirements: `pip install -r requirements.txt -r requirements-test.txt`
3. Run the tests: `bash run_test.sh -c -a`

This project uses the following QA tools:
- [PyTest](https://docs.pytest.org/en/latest/) - for running unit tests.
- [PyLint](https://www.pylint.org/) - for enforcing code style.
- [MyPy](http://mypy-lang.org/) - for static type checking.
- [Travis CI](https://travis-ci.org/) - for continuous integration.
- [Black](https://black.readthedocs.io/en/stable/) - for uniform code formatting.

# License
This project is distributed under the MIT license.
