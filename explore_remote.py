import paramiko
import time

host = "51.178.19.120"
user = "ubuntu"
password = "=OCf18e5zkGr@5O4"

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password)

    print(f"Conectado a {host}")

    # Listar directorios para encontrar el proyecto
    stdin, stdout, stderr = client.exec_command("ls -F")
    files = stdout.read().decode().splitlines()
    print("Archivos en home:")
    for f in files:
        print(f" - {f}")

    client.close()
except Exception as e:
    print(f"Error: {e}")
