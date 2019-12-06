"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from codecs import open
from os import path

from setuptools import find_packages, setup

import json_ref_dict


REQUIREMENTS_FILE_PATH = path.join(
    path.abspath(path.dirname(__file__)), "requirements.txt"
)

with open(REQUIREMENTS_FILE_PATH, "r") as f:
    REQUIREMENTS_FILE = [
        line
        for line in f.read().splitlines()
        if not line.startswith("#") and not line.startswith("--")
    ]

setup(
    name="json-ref-dict",
    version=json_ref_dict.__version__,
    description="Python dict-like object which abstracts resolution of JSONSchema references",
    author="Jack Smith",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
    ],
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    install_requires=REQUIREMENTS_FILE,
    dependency_links=[],
)
