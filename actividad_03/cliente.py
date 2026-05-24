import sys
from SocketTCP import SocketTCP


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 cliente.py <host> <puerto>", file=sys.stderr)
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    address = (host, port)

    client_socketTCP = SocketTCP()
    client_socketTCP.connect(address)

    print("Cliente terminó prueba de handshake")


if __name__ == "__main__":
    main()