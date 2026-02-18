import shutil
import importlib.util

print("Checking tools...")
sshpass = shutil.which("sshpass")
expect = shutil.which("expect")
paramiko_spec = importlib.util.find_spec("paramiko")

print(f"sshpass: {'Found' if sshpass else 'Not Found'}")
print(f"expect: {'Found' if expect else 'Not Found'}")
print(f"paramiko: {'Found' if paramiko_spec else 'Not Found'}")
