import errno
import re
import urllib.request

pat = r"({name}: Final)\[(int)\]"

code = urllib.request.urlopen(
    "https://raw.githubusercontent.com/python/typeshed/c7f70d8ac9310823a2fe5bbe0d276bac9eb314d3/stdlib/errno.pyi"
).read().decode()

ns = {}
exec(code, ns)
relevant_to_this_os = ns["__annotations__"]

for name, value in vars(errno).items():
    if name in relevant_to_this_os:
        code = re.sub(pat.format(name=name), rf"\g<1>[Literal[{value}]]", code)

print(code)

