import sys
import contextlib
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

    # Todo el debug interno de SocketTCP se redirige a stderr,
    # para que stdout quede limpio y contenga solo el archivo recibido.
    with contextlib.redirect_stdout(sys.stderr):
        connection_socketTCP, new_address = server_socketTCP.accept()
        print(f"Conexión aceptada en nuevo socket: {new_address}")

        received_file = connection_socketTCP.recv(10_000_000)

        # Para esta etapa NO llamamos recv_close()
        # El cierre con pérdidas se implementa en el siguiente paso
        connection_socketTCP.recv_close()
        print("Servidor: conexión cerrada")

    # Solo el contenido recibido se escribe en stdout
    sys.stdout.buffer.write(received_file)
    sys.stdout.buffer.flush()

    print("\nServidor: archivo recibido correctamente", file=sys.stderr)


if __name__ == "__main__":
    main()