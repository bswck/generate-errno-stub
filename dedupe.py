from contextlib import contextmanager
import sys
from itertools import product
from typing import Generator
from unittest.mock import patch
from collections import defaultdict

platforms = ["other", "linux", "darwin", "win32"]
versions = [
    None,
    (3, 10),
    (3, 11),
    (3, 12),
    (3, 13),
    (3, 14),
]  # first version always None

current_indent = 0
indent_width = 4
platform_guard_tpl = "if sys.platform == {platform}:"
version_guard_tpl = "if sys.version_info[:2] == {version}:"
annotation_tpl = "{name}: Final[Literal[{value}]]"

type Errnos = dict[str, dict[tuple[int, int], dict[str, str]]]

def get_errnos() -> Errnos:
    # {platform: {version: {name: value}}}
    errnos = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {})))

    combined_errnos_script = sys.argv[1]

    for platform, version in product(platforms, versions):
        prev_version = None
        if version:
            prev_version = versions[versions.index(version) - 1]
        with patch("sys.platform", platform), patch("sys.version_info", version):
            errnos_for_env = {}
            exec(combined_errnos_script, errnos_for_env)
            for name, value in sorted(errnos_for_env.items()):
                if version is None:
                    errnos[platform][version][name] = value
                elif prev_version_value := errnos[platform][prev_version].get(name):
                    if prev_version_value != value:
                        print(
                            f"! errno.{name} differed on {platform} between versions {prev_version} and {version}:",
                            file=sys.stderr,
                        )
                        print(f"! {prev_version}: {prev_version_value}", file=sys.stderr)
                        print(f"! {version}: {value}", file=sys.stderr)
                    else:
                        del errnos[platform][prev_version][name]
                    errnos[platform][version][name] = value


def emit(s: str) -> None:
    print(" " * current_indent, s)


@contextmanager
def indentation(only_if: bool = True) -> Generator[None]:
    global current_indent
    current_indent += indent_width * only_if
    yield
    current_indent -= indent_width * only_if


def produce_deduped_stub(errnos: Errnos) -> None:
    emit("import sys")
    emit("from typing import Final, Literal")

    for platform, versions in errnos.items():
        emit(platform_guard_tpl.format(platform=platform))

        with indentation():
            for version, names in versions.items():
                with indentation(only_if=version is not None):
                    if version:
                        emit(version_guard_tpl.format(version=version))

                    for name, value in names.items():
                        with indentation():
                            emit(annotation_tpl.format(name=name, value=value))


def main() -> None:
    produce_deduped_stub(get_errnos())


if __name__ == "__main__":
    main()
