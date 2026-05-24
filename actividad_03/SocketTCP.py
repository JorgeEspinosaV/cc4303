import socket
import random

MAX_DATA_SIZE = 16
UDP_BUFFER_SIZE = 1024
TIMEOUT = 1.0


class SocketTCP:
    def __init__(self):
        # Socket UDP interno: sobre esto construiremos nuestro "TCP simplificado"
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(TIMEOUT)

        # Dirección local, por ejemplo ("127.0.0.1", 8000)
        self.origin_address = None

        # Dirección de destino, por ejemplo ("127.0.0.1", 9000)
        self.destination_address = None

        # Número de secuencia inicial aleatorio entre 0 y 100
        self.seq = random.randint(0, 100)

        # Número de secuencia esperado desde la contraparte
        self.expected_seq = None

        # Variables que necesitaremos más adelante para recv(buff_size)
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
        segment = header + data

        return segment

    @staticmethod
    def parse_segment(segment):
        """
        Recibe un segmento en bytes y lo separa en sus partes:
        SYN, ACK, FIN, SEQ y DATA.
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