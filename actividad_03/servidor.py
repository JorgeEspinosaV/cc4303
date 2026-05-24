import socket
import sys

data_size = 16
UDP_size = 1024


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 servidor.py <puerto>", file=sys.stderr)
        sys.exit(1)

    port = int(sys.argv[1])
    address = ("127.0.0.1", port)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(address)

    print(f"Servidor UDP escuchando en {address}", file=sys.stderr, flush=True)

    while True:
        data, client_address = server_socket.recvfrom(UDP_size)

        print(f"\nRecibido desde {client_address}: {data!r}", file=sys.stderr, flush=True)

        if data == b"":
            break

        print(data.decode(errors="replace"), end="", flush=True)


if __name__ == "__main__":
    main()