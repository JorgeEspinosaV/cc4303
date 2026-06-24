import sys
import socket
import ipaddress


HEADER_SIZE = 20

round_robin_positions = {}
received_fragments = {}


def create_packet(parsed_packet):
    """
    create_packet(parsed_packet) -> bytes

    Crea un paquete IP en bytes usando el header de fragmentación.

    Header:
    - IP destino: 4 bytes
    - Puerto destino: 2 bytes
    - TTL: 1 byte
    - ID: 4 bytes
    - Offset: 4 bytes
    - Tamaño mensaje: 4 bytes
    - FLAG: 1 byte
    - Mensaje: n bytes
    """
    destination_ip = parsed_packet["destination_ip"]
    destination_port = parsed_packet["destination_port"]
    ttl = parsed_packet["ttl"]
    packet_id = parsed_packet["id"]
    offset = parsed_packet["offset"]
    size = parsed_packet["size"]
    flag = parsed_packet["flag"]
    message = parsed_packet["message"]

    if isinstance(message, str):
        message_bytes = message.encode("utf-8")
    else:
        message_bytes = message

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


def parse_packet(ip_packet):
    """
    parse_packet(ip_packet) -> dict

    Recibe un paquete en bytes y extrae los campos del header.

    Paso a paso:
    1. Verifica que el paquete tenga al menos 20 bytes de header.
    2. Extrae IP destino.
    3. Extrae puerto destino.
    4. Extrae TTL.
    5. Extrae ID.
    6. Extrae Offset.
    7. Extrae Tamaño.
    8. Extrae FLAG.
    9. Extrae el mensaje.
    """
    if len(ip_packet) < HEADER_SIZE:
        raise ValueError("El paquete es demasiado pequeño")

    destination_ip = socket.inet_ntoa(ip_packet[0:4])
    destination_port = int.from_bytes(ip_packet[4:6], byteorder="big")
    ttl = ip_packet[6]
    packet_id = int.from_bytes(ip_packet[7:11], byteorder="big")
    offset = int.from_bytes(ip_packet[11:15], byteorder="big")
    size = int.from_bytes(ip_packet[15:19], byteorder="big")
    flag = ip_packet[19]
    message = ip_packet[20:]

    return {
        "destination_ip": destination_ip,
        "destination_port": destination_port,
        "ttl": ttl,
        "id": packet_id,
        "offset": offset,
        "size": size,
        "flag": flag,
        "message": message,
    }


def check_routes(routes_file_name, destination_address):
    """
    check_routes(routes_file_name, destination_address) -> tuple | None

    Busca el siguiente salto y el MTU del enlace.

    Retorna:
        ((next_hop_ip, next_hop_port), mtu)

    Si no existe ruta:
        None
    """
    destination_ip, destination_port = destination_address
    matching_routes = []

    with open(routes_file_name, "r", encoding="utf-8") as routes_file:
        for line in routes_file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()

            if len(parts) != 6:
                continue

            network_text = parts[0]
            initial_port = int(parts[1])
            final_port = int(parts[2])
            next_hop_ip = parts[3]
            next_hop_port = int(parts[4])
            mtu = int(parts[5])

            network = ipaddress.ip_network(network_text, strict=False)
            destination_ip_object = ipaddress.ip_address(destination_ip)

            ip_matches = destination_ip_object in network
            port_matches = initial_port <= destination_port <= final_port

            if ip_matches and port_matches:
                matching_routes.append(((next_hop_ip, next_hop_port), mtu))

    if not matching_routes:
        return None

    key = (
        destination_ip,
        destination_port,
        tuple(matching_routes),
    )

    current_position = round_robin_positions.get(key, 0)
    selected_route = matching_routes[current_position % len(matching_routes)]

    round_robin_positions[key] = (
        current_position + 1
    ) % len(matching_routes)

    return selected_route


def fragment_IP_packet(ip_packet, mtu):
    """
    fragment_IP_packet(ip_packet, mtu) -> list

    Fragmenta un paquete IP si su tamaño total supera el MTU.

    Paso a paso:
    1. Si el paquete completo cabe en el MTU, retorna [ip_packet].
    2. Si no cabe, calcula cuántos bytes de mensaje caben por fragmento.
    3. Divide el mensaje en trozos.
    4. Crea un paquete nuevo para cada trozo.
    5. Ajusta offset, size y flag de cada fragmento.
    6. Retorna la lista de fragmentos.
    """
    if len(ip_packet) <= mtu:
        return [ip_packet]

    parsed_packet = parse_packet(ip_packet)
    message = parsed_packet["message"]

    max_message_size = mtu - HEADER_SIZE

    if max_message_size <= 0:
        raise ValueError("El MTU es demasiado pequeño para el header")

    fragments = []

    for start in range(0, len(message), max_message_size):
        end = start + max_message_size
        fragment_message = message[start:end]

        absolute_offset = parsed_packet["offset"] + start

        if end < len(message) or parsed_packet["flag"] == 1:
            flag = 1
        else:
            flag = 0

        fragment_packet = {
            "destination_ip": parsed_packet["destination_ip"],
            "destination_port": parsed_packet["destination_port"],
            "ttl": parsed_packet["ttl"],
            "id": parsed_packet["id"],
            "offset": absolute_offset,
            "size": len(fragment_message),
            "flag": flag,
            "message": fragment_message,
        }

        fragments.append(create_packet(fragment_packet))

    return fragments


def reassemble_IP_packet(fragment_list):
    """
    reassemble_IP_packet(fragment_list) -> bytes | None

    Intenta reensamblar un paquete original desde una lista de fragmentos.

    Paso a paso:
    1. Parsea todos los fragmentos.
    2. Ordena los fragmentos por offset.
    3. Si solo hay un fragmento completo, lo retorna.
    4. Verifica continuidad de offsets.
    5. Verifica que el último fragmento tenga FLAG 0.
    6. Une los mensajes.
    7. Retorna un paquete reensamblado.
    8. Si faltan fragmentos, retorna None.
    """
    if not fragment_list:
        return None

    parsed_fragments = [parse_packet(fragment) for fragment in fragment_list]
    parsed_fragments.sort(key=lambda fragment: fragment["offset"])

    if len(parsed_fragments) == 1:
        only_fragment = parsed_fragments[0]

        if only_fragment["offset"] == 0 and only_fragment["flag"] == 0:
            return fragment_list[0]

        return None

    expected_offset = 0
    message_parts = []

    for fragment in parsed_fragments:
        if fragment["offset"] != expected_offset:
            return None

        message_parts.append(fragment["message"])
        expected_offset += fragment["size"]

    last_fragment = parsed_fragments[-1]

    if last_fragment["flag"] != 0:
        return None

    full_message = b"".join(message_parts)
    first_fragment = parsed_fragments[0]

    reassembled_packet = {
        "destination_ip": first_fragment["destination_ip"],
        "destination_port": first_fragment["destination_port"],
        "ttl": first_fragment["ttl"],
        "id": first_fragment["id"],
        "offset": 0,
        "size": len(full_message),
        "flag": 0,
        "message": full_message,
    }

    return create_packet(reassembled_packet)


def get_message_as_text(parsed_packet):
    """
    get_message_as_text(parsed_packet) -> str

    Convierte el mensaje desde bytes a string.
    """
    return parsed_packet["message"].decode("utf-8", errors="replace")


def main():
    """
    main() -> None

    Ejecuta el router con soporte de fragmentación.

    Paso a paso:
    1. Lee IP, puerto y archivo de rutas desde sys.argv.
    2. Crea un socket UDP.
    3. Recibe paquetes en ciclo infinito.
    4. Descarta paquetes con TTL 0.
    5. Si el paquete es para este router, lo guarda por ID.
    6. Intenta reensamblar los fragmentos del mismo ID.
    7. Si logra reensamblar, imprime el mensaje.
    8. Si no es para este router, busca ruta y MTU.
    9. Decrementa el TTL.
    10. Fragmenta según el MTU.
    11. Envía cada fragmento al siguiente salto.
    """
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
            packet_id = parsed_packet["id"]

            if packet_id not in received_fragments:
                received_fragments[packet_id] = []

            received_fragments[packet_id].append(packet)

            reassembled_packet = reassemble_IP_packet(
                received_fragments[packet_id]
            )

            if reassembled_packet is None:
                print(
                    f"Fragmento recibido para ID {packet_id}. "
                    f"Esperando más fragmentos."
                )
                continue

            parsed_reassembled_packet = parse_packet(reassembled_packet)

            print(
                f"Mensaje recibido en {current_router_address}: "
                f"{get_message_as_text(parsed_reassembled_packet)}"
            )

            del received_fragments[packet_id]
            continue

        route_result = check_routes(routes_file, destination_address)

        if route_result is None:
            print(
                f"No hay rutas hacia {destination_address} "
                f"para paquete {packet}"
            )
            continue

        next_hop, mtu = route_result

        parsed_packet["ttl"] -= 1
        packet_with_updated_ttl = create_packet(parsed_packet)

        fragments = fragment_IP_packet(packet_with_updated_ttl, mtu)

        print(
            f"redirigiendo paquete con destino final {destination_address} "
            f"desde {current_router_address} hacia {next_hop} "
            f"con MTU {mtu}. Fragmentos generados: {len(fragments)}"
        )

        for fragment in fragments:
            router_socket.sendto(fragment, next_hop)


if __name__ == "__main__":
    main()