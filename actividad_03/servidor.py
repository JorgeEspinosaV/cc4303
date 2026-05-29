import sys
from SocketTCP import SocketTCP


EXPECTED_MESSAGE = (
    "Este es un mensaje largo para probar Stop and Wait con perdidas. "
    "Debe llegar completo aunque se pierdan paquetes artificialmente. "
    "La gracia es que cada segmento espera su ACK antes de continuar."
).encode()


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

    full_message = connection_socketTCP.recv(1000)

    print("Mensaje recibido:", full_message)

    if full_message == EXPECTED_MESSAGE:
        print("Test con pérdidas: Passed")
    else:
        print("Test con pérdidas: Failed")
        print("Esperado:", EXPECTED_MESSAGE)
        print("Recibido:", full_message)

  
    # Para esta etapa NO llamamos recv_close().
    # El cierre con pérdidas se implementa en el siguiente paso.
    
    connection_socketTCP.recv_close()
    print("Servidor cerró conexión")


if __name__ == "__main__":
    main()