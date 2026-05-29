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

    # Test 1
    buff_size = 16
    full_message = connection_socketTCP.recv(buff_size)
    print("Test 1 received:", full_message)

    if full_message == "Mensje de len=16".encode():
        print("Test 1: Passed")
    else:
        print("Test 1: Failed")

    # Test 2
    buff_size = 19
    full_message = connection_socketTCP.recv(buff_size)
    print("Test 2 received:", full_message)

    if full_message == "Mensaje de largo 19".encode():
        print("Test 2: Passed")
    else:
        print("Test 2: Failed")

    # Test 3
    buff_size = 14
    message_part_1 = connection_socketTCP.recv(buff_size)
    message_part_2 = connection_socketTCP.recv(buff_size)

    print("Test 3 received:", message_part_1 + message_part_2)

    if (message_part_1 + message_part_2) == "Mensaje de largo 19".encode():
        print("Test 3: Passed")
    else:
        print("Test 3: Failed")

    # Cierre de conexión
    connection_socketTCP.recv_close()

    print("Servidor cerró conexión")


if __name__ == "__main__":
    main()