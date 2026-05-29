import sys
from SocketTCP import SocketTCP


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 cliente.py <host> <puerto>", file=sys.stderr)
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    address = (host, port)

    # Lee el archivo desde entrada estándar.
    # Ejemplo:
    # python3 cliente.py localhost 8000 < archivo.txt
    message = sys.stdin.buffer.read()

    if len(message) == 0:
        print("Cliente: no se recibió contenido por stdin", file=sys.stderr)
        sys.exit(1)

    client_socketTCP = SocketTCP()
    client_socketTCP.connect(address)

    client_socketTCP.send(message)

    print("Cliente: archivo enviado correctamente", file=sys.stderr)

    # Para esta etapa NO cerramos la conexión,
    # porque el enunciado dice que las pérdidas pueden causar problemas con el cierre y que eso es esperable.
    client_socketTCP.close()

    print("Cliente: conexión cerrada", file=sys.stderr)


if __name__ == "__main__":
    main()
