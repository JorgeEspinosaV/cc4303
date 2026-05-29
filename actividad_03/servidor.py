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

    print(f"Servidor escuchando en {address}", file=sys.stderr)

    connection_socketTCP, new_address = server_socketTCP.accept()

    print(f"Conexión aceptada en nuevo socket: {new_address}", file=sys.stderr)

    # Tamaño suficientemente grande para esta prueba.
    # Si quieres recibir archivos enormes, habría que hacer un loop.
    received_file = connection_socketTCP.recv(10_000_000)

    # Imprime el archivo recibido en salida estándar.
    sys.stdout.buffer.write(received_file)
    sys.stdout.buffer.flush()

    print("\nServidor: archivo recibido correctamente", file=sys.stderr)

    # Para esta etapa NO llamamos recv_close().
    # El cierre con pérdidas se implementa en el siguiente paso.
    connection_socketTCP.recv_close()

    print("Servidor: conexión cerrada", file=sys.stderr)


if __name__ == "__main__":
    main()
