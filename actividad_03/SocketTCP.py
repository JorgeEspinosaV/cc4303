import socket
import random

MAX_DATA_SIZE = 16
UDP_BUFFER_SIZE = 1024
TIMEOUT = 1.0


class SocketTCP:
    def __init__(self):
        # Socket UDP interno
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(TIMEOUT)

        # Dirección local y dirección remota
        self.origin_address = None
        self.destination_address = None

        # Número de secuencia propio
        self.seq = random.randint(0, 100)

        # Número de secuencia esperado desde la contraparte
        self.expected_seq = None

        # Variables para recv(), las usaremos después
        self.pending_data = b""
        self.remaining_message_length = 0

    @staticmethod
    def create_segment(syn, ack, fin, seq, data=b""):
        """
        Crea un segmento con formato:
        SYN|||ACK|||FIN|||SEQ|||DATOS
        """

        if isinstance(data, str):
            data = data.encode()

        header = f"{int(syn)}|||{int(ack)}|||{int(fin)}|||{int(seq)}|||".encode()
        return header + data

    @staticmethod
    def parse_segment(segment):
        """
        Recibe un segmento en bytes y retorna un diccionario
        con SYN, ACK, FIN, SEQ y DATA.
        """

        parts = segment.split(b"|||", 4)

        syn = int(parts[0].decode())
        ack = int(parts[1].decode())
        fin = int(parts[2].decode())
        seq = int(parts[3].decode())
        data = parts[4]

        return {
            "SYN": syn,
            "ACK": ack,
            "FIN": fin,
            "SEQ": seq,
            "DATA": data,
        }

    def bind(self, address):
        """
        Asocia el socket UDP interno a una dirección local.
        Ejemplo: ("127.0.0.1", 8000)
        """

        self.origin_address = address
        self.udp_socket.bind(address)

    def connect(self, address):
        """
        Lado cliente del 3-way handshake.
        Envía SYN, recibe SYN-ACK y responde ACK.
        """

        # Al principio el cliente intenta conectarse a la dirección conocida del servidor
        self.destination_address = address

        # Paso 1: enviar SYN
        syn_segment = self.create_segment(
            syn=1,
            ack=0,
            fin=0,
            seq=self.seq,
            data=b""
        )

        print(f"[CLIENTE] Enviando SYN seq={self.seq}")

        self.udp_socket.sendto(syn_segment, self.destination_address)

        # Paso 2: esperar SYN-ACK
        while True:
            try:
                response, server_address = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(response)

                print(
                    f"[CLIENTE] Recibido: "
                    f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                    f"FIN={parsed['FIN']} SEQ={parsed['SEQ']} "
                    f"desde {server_address}"
                )

                if parsed["SYN"] == 1 and parsed["ACK"] == 1:
                    # Desde ahora el cliente debe hablar con el nuevo socket del servidor
                    self.destination_address = server_address

                    # El cliente espera que el próximo seq del servidor sea SEQ + 1
                    self.expected_seq = parsed["SEQ"] + 1

                    # Paso 3: enviar ACK final
                    self.seq += 1

                    ack_segment = self.create_segment(
                        syn=0,
                        ack=1,
                        fin=0,
                        seq=self.seq,
                        data=b""
                    )

                    print(f"[CLIENTE] Enviando ACK seq={self.seq}")

                    self.udp_socket.sendto(ack_segment, self.destination_address)

                    print("[CLIENTE] Handshake completado")
                    return

            except socket.timeout:
                print("[CLIENTE] Timeout esperando SYN-ACK. Reenviando SYN")
                self.udp_socket.sendto(syn_segment, self.destination_address)

    def accept(self):
        """
        Lado servidor del 3-way handshake.
        Espera SYN, crea un nuevo SocketTCP, responde SYN-ACK,
        espera ACK final y retorna el nuevo socket junto a su dirección.
        """

        print("[SERVIDOR] Esperando SYN...")

        while True:
            try:
                segment, client_address = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(segment)

                print(
                    f"[SERVIDOR] Recibido: "
                    f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                    f"FIN={parsed['FIN']} SEQ={parsed['SEQ']} "
                    f"desde {client_address}"
                )

                if parsed["SYN"] == 1:
                    # Crear nuevo socket para esta conexión
                    connection_socket = SocketTCP()

                    # El nuevo socket debe tener una dirección distinta.
                    # Usamos puerto 0 para que el sistema operativo elija uno libre.
                    connection_socket.bind(("127.0.0.1", 0))

                    new_address = connection_socket.udp_socket.getsockname()

                    # Guardamos la dirección del cliente
                    connection_socket.destination_address = client_address

                    # El servidor espera que el próximo seq del cliente sea SEQ + 1
                    connection_socket.expected_seq = parsed["SEQ"] + 1

                    # Paso 2: enviar SYN-ACK desde el nuevo socket
                    syn_ack_segment = connection_socket.create_segment(
                        syn=1,
                        ack=1,
                        fin=0,
                        seq=connection_socket.seq,
                        data=b""
                    )

                    print(
                        f"[SERVIDOR] Enviando SYN-ACK seq={connection_socket.seq} "
                        f"desde {new_address}"
                    )

                    connection_socket.udp_socket.sendto(
                        syn_ack_segment,
                        client_address
                    )

                    # Paso 3: esperar ACK final en el nuevo socket
                    while True:
                        try:
                            response, response_address = connection_socket.udp_socket.recvfrom(
                                UDP_BUFFER_SIZE
                            )
                            parsed_response = connection_socket.parse_segment(response)

                            print(
                                f"[SERVIDOR] Recibido en nuevo socket: "
                                f"SYN={parsed_response['SYN']} "
                                f"ACK={parsed_response['ACK']} "
                                f"FIN={parsed_response['FIN']} "
                                f"SEQ={parsed_response['SEQ']} "
                                f"desde {response_address}"
                            )

                            if parsed_response["ACK"] == 1:
                                connection_socket.seq += 1

                                print("[SERVIDOR] Handshake completado")
                                return connection_socket, new_address

                        except socket.timeout:
                            print("[SERVIDOR] Timeout esperando ACK final")
                            print("[SERVIDOR] Reenviando SYN-ACK")
                            connection_socket.udp_socket.sendto(
                                syn_ack_segment,
                                client_address
                            )

            except socket.timeout:
                # El servidor sigue esperando conexiones
                continue