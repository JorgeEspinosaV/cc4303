import sys
import socket
import ipaddress


round_robin_positions = {}


def create_packet(parsed_packet: dict) -> bytes:
    destination_ip = parsed_packet["destination_ip"]
    destination_port = parsed_packet["destination_port"]
    ttl = parsed_packet["ttl"]
    message = parsed_packet["message"]

    ip_bytes = socket.inet_aton(destination_ip)
    port_bytes = destination_port.to_bytes(2, byteorder="big")
    ttl_bytes = ttl.to_bytes(1, byteorder="big")
    message_bytes = message.encode("utf-8")

    return ip_bytes + port_bytes + ttl_bytes + message_bytes


def parse_packet(ip_packet: bytes) -> dict:
    if len(ip_packet) < 7:
        raise ValueError("El paquete es demasiado pequeño")

    destination_ip = socket.inet_ntoa(ip_packet[0:4])
    destination_port = int.from_bytes(ip_packet[4:6], byteorder="big")
    ttl = ip_packet[6]
    message = ip_packet[7:].decode("utf-8")

    return {
        "destination_ip": destination_ip,
        "destination_port": destination_port,
        "ttl": ttl,
        "message": message,
    }


def check_routes(routes_file_name, destination_address): 
    destination_ip, destination_port = destination_address
    matching_routes = []

    with open(routes_file_name, "r", encoding="utf-8") as routes_file:
        for line in routes_file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()

            if len(parts) != 5:
                continue

            network_text = parts[0]
            initial_port = int(parts[1])
            final_port = int(parts[2])
            next_hop_ip = parts[3]
            next_hop_port = int(parts[4])

            network = ipaddress.ip_network(network_text, strict=False)
            destination_ip_object = ipaddress.ip_address(destination_ip)

            ip_matches = destination_ip_object in network
            port_matches = initial_port <= destination_port <= final_port

            if ip_matches and port_matches:
                matching_routes.append((next_hop_ip, next_hop_port))

    if not matching_routes:
        return None

    key = (
        destination_ip,
        destination_port,
        tuple(matching_routes),
    )

    current_position = round_robin_positions.get(key, 0)

    selected_route = matching_routes[
        current_position % len(matching_routes)
    ]

    round_robin_positions[key] = (
        current_position + 1
    ) % len(matching_routes)

    return selected_route


def main():
    if len(sys.argv) != 4:
        print("Uso: python3 router.py router_IP router_puerto archivo_rutas")
        sys.exit(1)

    router_ip = sys.argv[1]
    router_port = int(sys.argv[2])
    routes_file = sys.argv[3]

    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind((router_ip, router_port))

    current_router_address = (router_ip, router_port)

    print(f"Router escuchando en {router_ip}:{router_port}")
    print(f"Usando tabla de rutas: {routes_file}")

    while True:
        packet, sender_address = router_socket.recvfrom(65535)

        try:
            parsed_packet = parse_packet(packet)
        except (ValueError, UnicodeDecodeError) as error:
            print(f"Paquete inválido desde {sender_address}: {error}")
            continue

        destination_address = (
            parsed_packet["destination_ip"],
            parsed_packet["destination_port"],
        )

        if parsed_packet["ttl"] == 0:
            print(f"Se recibió paquete {packet} con TTL 0")
            continue

        if destination_address == current_router_address:
            print(f"Mensaje recibido en {current_router_address}: {parsed_packet['message']}")
            continue

        next_hop = check_routes(routes_file, destination_address)

        if next_hop is None:
            print(
                f"No hay rutas hacia {destination_address} "
                f"para paquete {packet}"
            )
            continue

        parsed_packet["ttl"] -= 1
        forwarded_packet = create_packet(parsed_packet)

        print(
            f"redirigiendo paquete {forwarded_packet} "
            f"con destino final {destination_address} "
            f"desde {current_router_address} "
            f"hacia {next_hop}"
        )

        router_socket.sendto(forwarded_packet, next_hop)


if __name__ == "__main__":
    main()