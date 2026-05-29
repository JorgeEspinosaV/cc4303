import sys
from SocketTCP import SocketTCP


EXPECTED_MESSAGE = (
    "Este es un mensaje largo para probar Stop and Wait con perdidas. "
    "Debe llegar completo aunque se pierdan paquetes artificialmente. "
    "La gracia es que cada segmento espera su ACK antes de continuar."
).encode()


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 cliente.py <host> <puerto>", file=sys.stderr)
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    address = (host, port)

    client_socketTCP = SocketTCP()
    client_socketTCP.connect(address)

    client_socketTCP.send(EXPECTED_MESSAGE)

    print("Cliente terminó envío con pérdidas")

    # Para esta etapa NO cerramos la conexión,
    # porque el enunciado dice que las pérdidas pueden causar problemas con el cierre y que eso es esperable.
    client_socketTCP.close()
    print("Cliente cerró conexión")


if __name__ == "__main__":
    main()