"""Third-party compatibility shims applied before inference imports."""

from __future__ import annotations


def apply_compat_patches() -> None:
    # madmom 0.16 still imports MutableSequence from collections (removed in Py3.10+).
    import collections
    import collections.abc

    if not hasattr(collections, "MutableSequence"):
        collections.MutableSequence = collections.abc.MutableSequence

    # madmom 0.16 uses deprecated NumPy aliases removed in 1.24+ (np.float, etc.).
    import numpy as np

    _numpy_aliases = {
        "float": np.float64,
        "int": np.int64,
        "bool": np.bool_,
        "complex": np.complex128,
        "object": object,
        "str": str,
    }
    for name, target in _numpy_aliases.items():
        if not hasattr(np, name):
            setattr(np, name, target)


apply_compat_patches()
