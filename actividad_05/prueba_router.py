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
    if len(sys.argv) != 4:
        print(
            "Uso: python3 prueba_router.py "
            "IP_destino;puerto_destino;TTL "
            "IP_router_inicial puerto_router_inicial"
        )
        sys.exit(1)

    headers = sys.argv[1]
    initial_router_ip = sys.argv[2]
    initial_router_port = int(sys.argv[3])

    destination_ip, destination_port_text, ttl_text = headers.split(";")
    destination_port = int(destination_port_text)
    ttl = int(ttl_text)

    sender_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("Escribe mensajes. Para terminar usa Ctrl + D.")

    for line in sys.stdin:
        message = line.strip()

        if not message:
            continue

        packet = create_packet(
            destination_ip,
            destination_port,
            ttl,
            message,
        )

        sender_socket.sendto(
            packet,
            (initial_router_ip, initial_router_port),
        )

        print(f"Enviado: {message}")


if __name__ == "__main__":
    main()