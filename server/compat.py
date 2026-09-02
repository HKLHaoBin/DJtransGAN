"""Third-party compatibility shims applied before inference imports."""

from __future__ import annotations


def apply_compat_patches() -> None:
    # madmom 0.16 still imports MutableSequence from collections (removed in Py3.10+).
    import collections
    import collections.abc

    if not hasattr(collections, "MutableSequence"):
        collections.MutableSequence = collections.abc.MutableSequence


apply_compat_patches()
