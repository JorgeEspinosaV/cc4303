import socket
import sys


def create_packet(
    destination_ip: str,
    destination_port: int,
    ttl: int,
    message: str,
) -> bytes:
    ip_bytes = socket.inet_aton(destination_ip)
    port_bytes = destination_port.to_bytes(2, byteorder="big")
    ttl_bytes = ttl.to_bytes(1, byteorder="big")
    message_bytes = message.encode("utf-8")

    return ip_bytes + port_bytes + ttl_bytes + message_bytes


def main():
    if len(sys.argv) != 7:
        print(
            "Uso: python3 enviar.py "
            "IP_destino puerto_destino TTL mensaje "
            "IP_router_inicial puerto_router_inicial"
        )
        sys.exit(1)

    destination_ip = sys.argv[1]
    destination_port = int(sys.argv[2])
    ttl = int(sys.argv[3])
    message = sys.argv[4]
    initial_router_ip = sys.argv[5]
    initial_router_port = int(sys.argv[6])

    packet = create_packet(
        destination_ip,
        destination_port,
        ttl,
        message,
    )

    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sender_socket.sendto(
        packet,
        (initial_router_ip, initial_router_port),
    )

    print("Paquete enviado")


if __name__ == "__main__":
    main()