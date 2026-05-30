import sys
from SocketTCP import SocketTCP


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 servidor.py <puerto>", file=sys.stderr)
        sys.exit(1)

    port = int(sys.argv[1])
    address = ("127.0.0.1", port)

    server_socketTCP = SocketTCP()
    server_socketTCP.bind(address)

    print(f"Servidor escuchando en {address}")

    connection_socketTCP, new_address = server_socketTCP.accept()

    print(f"Conexión aceptada en nuevo socket: {new_address}")
    print("Servidor terminó prueba de handshake")


if __name__ == "__main__":
    main()