from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple
from unittest.mock import patch

if TYPE_CHECKING:
    from _typeshed import StrPath

# this is basically useless until we examine all platforms
all_platforms = ["linux", "darwin", "win32"]
all_versions = [(3, 10), (3, 11), (3, 12), (3, 13), (3, 14)]

current_indent = 0
indent_width = 4
literal_annotation_tpl = "{name}: Final[Literal[{value}]]"
relaxed_annotation_tpl = "{name}: Final[int]"  # unused


def emit(s: str) -> None:
    print(" " * current_indent, s)


@contextmanager
def indent(only_if: bool = True) -> Generator[None]:
    global current_indent
    current_indent += indent_width * only_if
    yield
    current_indent -= indent_width * only_if


class VersionRange(NamedTuple):
    versions: list[tuple[int, int]]

    def to_expression(self) -> str:
        atom = "sys.version_info()[:2]"
        match self.versions:
            case [single]:
                if single == all_versions[-1]:
                    return f"{atom} >= {single}"
                if single == all_versions[0]:
                    return ""
                return f"{atom} == {single}"
            case full if full == all_versions:
                return ""
            case [first, *rest, last]:
                f_maj, f_min = first
                l_maj, l_min = last
                assert f_maj == l_maj
                assert f_min + 1 + len(rest) == l_min
                assert last == all_versions[-1]
                return f"{atom} >= {first}"
            case r:
                raise AssertionError(f"invalid version range: {r}")


class PlatformRange(NamedTuple):
    platforms: list[str]

    def to_expression(self) -> str:
        atom = "sys.platform"
        match self.platforms:
            case full if full == all_platforms:
                return ""
            case [*targeted_platforms] if len(targeted_platforms) >= 1:
                # question: would type checkers understand membership test?
                # note: we'd need to create "generalizations" with windows specialcased... unless we check all systems
                return " or ".join(
                    [
                        f"{atom} == {platform.join('""')}"
                        for platform in targeted_platforms
                    ]
                )
            case _:
                raise AssertionError("no platforms")


def dedupe_from_script(script_path: StrPath) -> None:
    # {name: {value: {platform: [version, ...]}}}
    by_name: dict[str, dict[int, dict[str, list[tuple[int, int]]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    script = Path(script_path).read_text()

    for platform, version in product(all_platforms, all_versions):
        with patch("sys.platform", platform), patch("sys.version_info", version):
            errnos_for_env: dict[str, int] = {}
            exec(script, errnos_for_env)

            for name, value in sorted(errnos_for_env.items()):
                if name.isupper():
                    by_name[name][value][platform].append(version)

    if by_name:
        emit("import sys")
        emit("from typing import Final, Literal")

    conditional_blocks: dict[str, list[str]] = defaultdict(list)

    for name, values in by_name.items():
        for value, platforms in values.items():
            platform_range = PlatformRange(list(platforms))
            platform_clause = platform_range.to_expression()
            version_clauses = set()
            for platform, versions in platforms.items():
                version_range = VersionRange(versions)
                version_clause = version_range.to_expression()
                version_clauses.add(version_clause)
            if len(version_clauses) > 1:
                raise AssertionError(
                    "same value of same errno was introduced in different python version"
                )
            relevant_clauses = list(filter(bool, (platform_clause, version_clause)))
            clause = " and ".join(
                [
                    subclause.join(
                        "()"
                        if " or " in subclause and len(relevant_clauses) > 1
                        else ("", "")
                    )
                    for subclause in relevant_clauses
                ]
            )
            conditional_blocks[clause].append(
                literal_annotation_tpl.format(name=name, value=value)
            )

    for condition, statements in conditional_blocks.items():
        if condition:
            emit(f"if {condition}:")
        with indent(only_if=bool(condition)):
            for statement in statements:
                emit(statement)


def main(script_path: StrPath) -> None:
    dedupe_from_script(script_path)


if __name__ == "__main__":
    main(sys.argv[1])
