import errno
import sys

from textwrap import indent

guard = f'if sys.platform == "{sys.platform}" and sys.version_info[:2] == {tuple(sys.version_info)[:2]}:'
anns = []
tpl = "{name}: Final[Literal[{val}]] = {val}"

for name, val in vars(errno).items():
    if name.isupper():
        anns.append(tpl.format(name=name, val=val))

ann_code = "\n".join(sorted(anns))
full_block = "\n".join([guard, indent(ann_code, " " * 4)])
print(full_block)
