from __future__ import annotations

import difflib
import re
import sys
import errno
from bisect import insort
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrPath

literal_pattern = re.compile(r"(Final\[Literal\[(\d+)\]\])")
general_pattern = re.compile(r"(([\w]+): Final\[int\])")


def verify_stub(stub_path: StrPath) -> int:
    stub_code = Path(stub_path).read_text()
    stub_code = literal_pattern.sub(r"\g<1> = \g<2>", stub_code)
    stub_code = general_pattern.sub(r"\g<1> = errno.\g<2>", stub_code)
    expected: dict[str, int] = {}
    print("running patched code:", file=sys.stderr)
    print(stub_code, file=sys.stderr)
    exec(stub_code, {"errno": errno}, expected)
    if not expected:
        msg = "found no expected codes"
        raise AssertionError(msg)
    all_expected = sorted(
        [f"{name} = {val}" for name, val in expected.items() if name.isupper()]
    )
    print("\nexpecting:", file=sys.stderr)
    print("\n".join(all_expected) + "\n", file=sys.stderr)
    all_covered: list[str] = []
    all_extras: list[str] = []
    for name, val in vars(errno).items():
        line = f"{name} = {val}"
        if name in expected:
            insort(all_covered, line)
        elif name.isupper():
            insort(all_extras, line)
    diffs = tuple(
        difflib.context_diff(all_expected, all_covered + all_extras, lineterm="")
    )
    if diffs:
        print("checks didn't pass :(", file=sys.stderr)
        for diff in diffs:
            print(diff, file=sys.stderr)
        return 1
    print("checks passed!", file=sys.stderr)
    return 0


def main(stub_path: StrPath) -> int:
    return verify_stub(stub_path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
