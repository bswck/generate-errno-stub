from __future__ import annotations

import difflib
import re
import sys
from bisect import insort
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrPath

pat = re.compile(r"(Final\[Literal\[(\d+)\]\])")


def verify_stub(stub_path: StrPath) -> None:
    stub_code = Path(stub_path).read_text()
    stub_code_reified = pat.sub(r"\g<1> = \g<2>", stub_code)
    expected: dict[str, int] = {}
    exec(stub_code_reified, expected)
    if not expected:
        msg = "found no expected codes"
        raise AssertionError(msg)
    all_expected = sorted(
        [f"{name} = {val}" for name, val in expected.items() if name.isupper()]
    )
    import errno

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
        return
    print("checks passed!", file=sys.stderr)


def main(stub_path: StrPath) -> None:
    verify_stub(stub_path)


if __name__ == "__main__":
    main(sys.argv[1])
