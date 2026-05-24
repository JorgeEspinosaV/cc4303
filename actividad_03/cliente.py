import socket
import sys

data_size = 16


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 cliente.py <host> <puerto>", file=sys.stderr)
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    server_address = (host, port)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    message = sys.stdin.buffer.read()

    print(f"Cliente: se leyeron {len(message)} bytes", file=sys.stderr, flush=True)

    for i in range(0, len(message), data_size):
        chunk = message[i:i + data_size]
        print(f"Cliente: enviando {chunk!r}", file=sys.stderr, flush=True)
        client_socket.sendto(chunk, server_address)

    client_socket.close()


if __name__ == "__main__":
    main()