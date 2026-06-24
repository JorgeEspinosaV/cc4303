import socket
import sys


def create_packet(
    destination_ip,
    destination_port,
    ttl,
    packet_id,
    offset,
    size,
    flag,
    message,
):
    """
    create_packet(destination_ip, destination_port, ttl, packet_id, offset, size, flag, message) -> bytes

    Crea un paquete en bytes con header de fragmentación.
    """
    message_bytes = message.encode("utf-8")

    ip_bytes = socket.inet_aton(destination_ip)
    port_bytes = destination_port.to_bytes(2, byteorder="big")
    ttl_bytes = ttl.to_bytes(1, byteorder="big")
    id_bytes = packet_id.to_bytes(4, byteorder="big")
    offset_bytes = offset.to_bytes(4, byteorder="big")
    size_bytes = size.to_bytes(4, byteorder="big")
    flag_bytes = flag.to_bytes(1, byteorder="big")

    return (
        ip_bytes
        + port_bytes
        + ttl_bytes
        + id_bytes
        + offset_bytes
        + size_bytes
        + flag_bytes
        + message_bytes
    )


def main():
    """
    main() -> None

    Envía un paquete individual hacia el router inicial.

    Uso:
        python3 enviar.py IP_destino puerto_destino TTL ID OFFSET FLAG mensaje IP_router_inicial puerto_router_inicial
    """
    if len(sys.argv) != 10:
        print(
            "Uso: python3 enviar.py "
            "IP_destino puerto_destino TTL ID OFFSET FLAG mensaje "
            "IP_router_inicial puerto_router_inicial"
        )
        sys.exit(1)

    destination_ip = sys.argv[1]
    destination_port = int(sys.argv[2])
    ttl = int(sys.argv[3])
    packet_id = int(sys.argv[4])
    offset = int(sys.argv[5])
    flag = int(sys.argv[6])
    message = sys.argv[7]
    initial_router_ip = sys.argv[8]
    initial_router_port = int(sys.argv[9])

    size = len(message.encode("utf-8"))

    packet = create_packet(
        destination_ip,
        destination_port,
        ttl,
        packet_id,
        offset,
        size,
        flag,
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