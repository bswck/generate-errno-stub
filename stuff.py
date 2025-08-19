import os

prog = r"C:\Windows\System32\whoami.exe"
os.execve(prog, [prog], os.environ)
