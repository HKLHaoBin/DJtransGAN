"""PyInstaller runtime hook: madmom + NumPy compatibility shims for Python 3.10+."""

import collections
import collections.abc

if not hasattr(collections, "MutableSequence"):
    collections.MutableSequence = collections.abc.MutableSequence

import numpy as np

for _name, _target in {
    "float": np.float64,
    "int": np.int64,
    "bool": np.bool_,
    "complex": np.complex128,
    "object": object,
    "str": str,
}.items():
    if not hasattr(np, _name):
        setattr(np, _name, _target)
