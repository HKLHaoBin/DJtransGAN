"""PyInstaller runtime hook: madmom collections shim for Python 3.10+."""

import collections
import collections.abc

if not hasattr(collections, "MutableSequence"):
    collections.MutableSequence = collections.abc.MutableSequence
