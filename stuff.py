import os
import sys

os.execve(sys.executable, [sys.executable, "-V"], {"foo": "bar"})
