import socket
import random
import time
from CongestionControl import *

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

    def send_using_stop_and_wait(self, message):
        message = message.encode()

        total_length = len(message)

        # Enviar largo total
        seg = self.create_segment(syn=0, ack=0, fin=0, seq=self.seq,
                                  data=str(total_length).encode())
        while True:
            self.udp_socket.sendto(seg, self.destination_address)
            try:
                resp, _ = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(resp)
                if parsed["ACK"] == 1 and parsed["SEQ"] == self.seq + 1:
                    self.seq += 1
                    break
            except socket.timeout:
                continue

        # Enviar datos en chunks
        offset = 0
        while offset < total_length:
            chunk = message[offset: offset + MAX_DATA_SIZE]
            seg = self.create_segment(syn=0, ack=0, fin=0, seq=self.seq, data=chunk)
            while True:
                self.udp_socket.sendto(seg, self.destination_address)
                try:
                    resp, _ = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                    parsed = self.parse_segment(resp)
                    if parsed["ACK"] == 1 and parsed["SEQ"] == self.seq + len(chunk):
                        self.seq += len(chunk)
                        offset += len(chunk)
                        break
                except socket.timeout:
                    continue

    def recv_using_stop_and_wait(self, buff_size):
        # Recibir largo total
        while True:
            try:
                segment, _ = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(segment)
                if parsed["SEQ"] == self.expected_seq:
                    total_length = int(parsed["DATA"].decode())
                    self.expected_seq += 1
                    ack = self.create_segment(syn=0, ack=1, fin=0, seq=self.expected_seq)
                    self.udp_socket.sendto(ack, self.destination_address)
                    break
                else:
                    ack = self.create_segment(syn=0, ack=1, fin=0, seq=self.expected_seq)
                    self.udp_socket.sendto(ack, self.destination_address)
            except socket.timeout:
                continue

        # Recibir datos
        received = b""
        while len(received) < total_length:
            try:
                segment, _ = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(segment)
                if parsed["SEQ"] == self.expected_seq:
                    received += parsed["DATA"]
                    self.expected_seq += len(parsed["DATA"])
                    ack = self.create_segment(syn=0, ack=1, fin=0, seq=self.expected_seq)
                    self.udp_socket.sendto(ack, self.destination_address)
                else:
                    ack = self.create_segment(syn=0, ack=1, fin=0, seq=self.expected_seq)
                    self.udp_socket.sendto(ack, self.destination_address)
            except socket.timeout:
                continue

        return received[:buff_size]


    def send_using_go_back_n(self, message):
        if isinstance(message, str):
            message = message.encode()

        total_length = len(message)
        cc = CongestionControl(MSS=MAX_DATA_SIZE)

        # Dividir en chunks
        chunks = []
        offset = 0
        while offset < total_length:
            chunks.append(message[offset: offset + MAX_DATA_SIZE])
            offset += MAX_DATA_SIZE

        # Enviar largo total, stop & wait simple
        seg = self.create_segment(syn=0, ack=0, fin=0, seq=self.seq,
                                  data=str(total_length).encode())
        while True:
            self.udp_socket.sendto(seg, self.destination_address)
            try:
                resp, _ = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(resp)
                if parsed["ACK"] == 1 and parsed["SEQ"] == self.seq + 1:
                    self.seq += 1
                    break
            except socket.timeout:
                continue

        # Calcular número de secuencia para cada chunk
        def seq_of(idx):
            return self.seq + sum(len(chunks[i]) for i in range(idx))

        # Go back n con ventana de congestión
        base = 0
        next_idx = 0
        timers = {}

        self.udp_socket.settimeout(0.05)

        while base < len(chunks):
            cwnd_segs = max(1, cc.get_MSS_in_cwnd())

            # Enviar segmentos que caben en la ventana
            while next_idx < base + cwnd_segs and next_idx < len(chunks):
                chunk = chunks[next_idx]
                seg = self.create_segment(syn=0, ack=0, fin=0,
                                          seq=seq_of(next_idx), data=chunk)
                self.udp_socket.sendto(seg, self.destination_address)
                timers[next_idx] = time.time()
                next_idx += 1

            # Intentar recibir ACK
            try:
                resp, _ = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(resp)

                if parsed["ACK"] == 1:
                    acked_seq = parsed["SEQ"]
                    # Avanzar base por todos los chunks confirmados
                    while base < len(chunks) and acked_seq >= seq_of(base + 1):
                        cc.event_ack_received()
                        timers.pop(base, None)
                        base += 1

            except socket.timeout:
                pass

            # Revisar timeouts
            now = time.time()
            timed_out = any(
                now - timers[idx] > TIMEOUT
                for idx in range(base, next_idx)
                if idx in timers
            )

            if timed_out:
                cc.event_timeout()
                # Retroceder ventama
                next_idx = base
                timers.clear()

        self.seq += sum(len(c) for c in chunks)
        self.udp_socket.settimeout(TIMEOUT)

    def recv_using_go_back_n(self, buff_size):
        # El receptor GBN solo acepta en orden
        return self.recv_using_stop_and_wait(buff_size)

    def send(self, message, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        elif mode == "go_back_n":
            self.send_using_go_back_n(message)

    def recv(self, buff_size, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)
