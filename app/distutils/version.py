"""Small subset of distutils.version used by undetected-chromedriver.

This provides a LooseVersion-compatible class for environments where
``distutils`` was removed from the standard library.
"""

from __future__ import annotations

from functools import total_ordering
import re


@total_ordering
class LooseVersion:
    component_re = re.compile(r"(\d+|[a-zA-Z]+|\.)")

    def __init__(self, vstring: str | bytes | "LooseVersion") -> None:
        if isinstance(vstring, LooseVersion):
            vstring = vstring.vstring
        if isinstance(vstring, bytes):
            vstring = vstring.decode()
        self.vstring = str(vstring)
        self.version = self.parse(self.vstring)

    def parse(self, vstring: str):
        parts = []
        for part in self.component_re.split(vstring):
            if not part or part == ".":
                continue
            if part.isdigit():
                parts.append(int(part))
            else:
                parts.append(part.lower())
        return parts

    def _cmp_tuple(self):
        normalized = []
        for part in self.version:
            if isinstance(part, int):
                normalized.append((0, part))
            else:
                normalized.append((1, part))
        return tuple(normalized)

    def __eq__(self, other):
        other = other if isinstance(other, LooseVersion) else LooseVersion(other)
        return self._cmp_tuple() == other._cmp_tuple()

    def __lt__(self, other):
        other = other if isinstance(other, LooseVersion) else LooseVersion(other)
        return self._cmp_tuple() < other._cmp_tuple()

    def __repr__(self) -> str:
        return f"LooseVersion ('{self.vstring}')"
