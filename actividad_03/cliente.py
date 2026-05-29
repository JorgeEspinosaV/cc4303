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

    # Test 1
    message = "Mensje de len=16".encode()
    client_socketTCP.send(message)

    # Test 2
    message = "Mensaje de largo 19".encode()
    client_socketTCP.send(message)

    # Test 3
    message = "Mensaje de largo 19".encode()
    client_socketTCP.send(message)

    print("Cliente terminó pruebas send/recv")

    # Cierre de conexión
    client_socketTCP.close()

    print("Cliente cerró conexión")


if __name__ == "__main__":
    main()