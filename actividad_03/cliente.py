import socket
import sys
from SocketTCP import SocketTCP

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

    seq = 0

    for i in range(0, len(message), data_size):
        chunk = message[i:i + data_size]

        segment = SocketTCP.create_segment(
            syn=0,
            ack=0,
            fin=0,
            seq=seq,
            data=chunk
        )

        print(f"Cliente: enviando segmento seq={seq}, data={chunk!r}", file=sys.stderr, flush=True)

        client_socket.sendto(segment, server_address)

        seq += len(chunk)

    client_socket.close()


if __name__ == "__main__":
    main()