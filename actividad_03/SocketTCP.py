import socket
import random
import time 

MAX_DATA_SIZE = 16
UDP_BUFFER_SIZE = 1024
TIMEOUT = 1.0

# Para probar pérdidas manuales.
# 0.2 = 20% de pérdida artificial.
# Cuando termines las pruebas puedes dejarlo en 0.0.
LOSS_PROBABILITY = 0.2
DEBUG_LOSS = True


class SocketTCP:
    def __init__(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.settimeout(TIMEOUT)

        self.origin_address = None
        self.destination_address = None

        self.seq = random.randint(0, 100)
        self.expected_seq = None

        self.pending_data = b""
        self.remaining_message_length = 0

        # Segmentos que llegaron antes de tiempo.
        # Sirve para el caso borde del último ACK perdido en el handshake.
        self.pending_segments = []

    @staticmethod
    def create_segment(syn, ack, fin, seq, data=b""):
        if isinstance(data, str):
            data = data.encode()

        header = f"{int(syn)}|||{int(ack)}|||{int(fin)}|||{int(seq)}|||".encode()
        return header + data

    @staticmethod
    def parse_segment(segment):
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

    def _sendto(self, segment, address):
        """
        Envía un segmento, pero puede simular pérdida manual.
        Esto reemplaza a self.udp_socket.sendto(...).
        """

        if LOSS_PROBABILITY > 0 and random.random() < LOSS_PROBABILITY:
            if DEBUG_LOSS:
                print(f"[LOSS] Paquete perdido artificialmente hacia {address}: {segment!r}")
            return 0

        return self.udp_socket.sendto(segment, address)

    def _recvfrom_or_pending(self):
        """
        Primero entrega segmentos guardados.
        Si no hay segmentos pendientes, lee desde el socket UDP.
        """

        if self.pending_segments:
            return self.pending_segments.pop(0)

        return self.udp_socket.recvfrom(UDP_BUFFER_SIZE)

    def bind(self, address):
        self.origin_address = address
        self.udp_socket.bind(address)

    def connect(self, address):
        """
        Lado cliente del 3-way handshake.
        Maneja pérdida de SYN y SYN-ACK mediante retransmisión.
        """

        self.destination_address = address

        syn_segment = self.create_segment(
            syn=1,
            ack=0,
            fin=0,
            seq=self.seq,
            data=b""
        )

        while True:
            print(f"[CLIENTE] Enviando SYN seq={self.seq}")
            self._sendto(syn_segment, self.destination_address)

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
                    # Desde ahora se habla con el nuevo socket del servidor.
                    self.destination_address = server_address
                    self.expected_seq = parsed["SEQ"] + 1

                    self.seq += 1

                    ack_segment = self.create_segment(
                        syn=0,
                        ack=1,
                        fin=0,
                        seq=self.seq,
                        data=b""
                    )

                    print(f"[CLIENTE] Enviando ACK final seq={self.seq}")
                    self._sendto(ack_segment, self.destination_address)

                    print("[CLIENTE] Handshake completado")
                    return

            except socket.timeout:
                print("[CLIENTE] Timeout esperando SYN-ACK. Reintentando handshake...")

    def accept(self):
        """
        Lado servidor del 3-way handshake.

        Caso normal:
        SYN -> SYN-ACK -> ACK

        Caso borde:
        Si se pierde el ACK final, el cliente puede empezar a enviar datos.
        Si el servidor recibe DATA con el SEQ esperado mientras espera ACK,
        asume que el ACK final se perdió, acepta la conexión y guarda ese DATA
        para que recv() lo procese después.
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
                    connection_socket = SocketTCP()
                    connection_socket.bind(("127.0.0.1", 0))

                    new_address = connection_socket.udp_socket.getsockname()

                    connection_socket.destination_address = client_address
                    connection_socket.expected_seq = parsed["SEQ"] + 1

                    syn_ack_segment = connection_socket.create_segment(
                        syn=1,
                        ack=1,
                        fin=0,
                        seq=connection_socket.seq,
                        data=b""
                    )

                    while True:
                        print(
                            f"[SERVIDOR] Enviando SYN-ACK seq={connection_socket.seq} "
                            f"desde {new_address}"
                        )

                        connection_socket._sendto(
                            syn_ack_segment,
                            client_address
                        )

                        try:
                            response, response_address = connection_socket._recvfrom_or_pending()
                            parsed_response = connection_socket.parse_segment(response)

                            print(
                                f"[SERVIDOR] Recibido en nuevo socket: "
                                f"SYN={parsed_response['SYN']} "
                                f"ACK={parsed_response['ACK']} "
                                f"FIN={parsed_response['FIN']} "
                                f"SEQ={parsed_response['SEQ']} "
                                f"DATA={parsed_response['DATA']!r} "
                                f"desde {response_address}"
                            )

                            # Caso normal: llegó ACK final.
                            if parsed_response["ACK"] == 1:
                                connection_socket.seq += 1

                                print("[SERVIDOR] Handshake completado")
                                return connection_socket, new_address

                            # Caso borde: se perdió ACK final, pero llegó DATA.
                            elif (
                                parsed_response["SYN"] == 0
                                and parsed_response["ACK"] == 0
                                and parsed_response["FIN"] == 0
                                and parsed_response["SEQ"] == connection_socket.expected_seq
                            ):
                                print("[SERVIDOR] Llegaron datos antes del ACK final.")
                                print("[SERVIDOR] Se asume que el ACK final del handshake se perdió.")
                                print("[SERVIDOR] Guardando primer segmento para recv().")

                                connection_socket.pending_segments.append(
                                    (response, response_address)
                                )

                                connection_socket.seq += 1

                                print("[SERVIDOR] Handshake completado por llegada de datos")
                                return connection_socket, new_address

                        except socket.timeout:
                            print("[SERVIDOR] Timeout esperando ACK final. Reenviando SYN-ACK...")

            except socket.timeout:
                continue

    def _send_ack(self, ack_seq):
        ack_segment = self.create_segment(
            syn=0,
            ack=1,
            fin=0,
            seq=ack_seq,
            data=b""
        )

        self._sendto(ack_segment, self.destination_address)

    def _send_with_stop_and_wait(self, payload):
        """
        Envía un payload usando Stop & Wait.
        Envía el segmento y espera ACK.
        Si no llega ACK por timeout, retransmite.
        """

        expected_ack = self.seq + len(payload)

        segment = self.create_segment(
            syn=0,
            ack=0,
            fin=0,
            seq=self.seq,
            data=payload
        )

        while True:
            print(
                f"[SEND] Enviando segmento seq={self.seq}, "
                f"esperando ACK={expected_ack}, data={payload!r}"
            )

            self._sendto(segment, self.destination_address)

            try:
                response, sender_address = self._recvfrom_or_pending()
                parsed = self.parse_segment(response)

                print(
                    f"[SEND] Recibido: "
                    f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                    f"FIN={parsed['FIN']} SEQ={parsed['SEQ']}"
                )

                # Caso borde: al cliente le llega SYN-ACK duplicado porque
                # se perdió el ACK final del handshake.
                if parsed["SYN"] == 1 and parsed["ACK"] == 1:
                    print("[SEND] SYN-ACK duplicado recibido. Reenviando ACK final.")

                    ack_segment = self.create_segment(
                        syn=0,
                        ack=1,
                        fin=0,
                        seq=self.seq,
                        data=b""
                    )

                    self._sendto(ack_segment, sender_address)
                    continue

                if parsed["ACK"] == 1 and parsed["SEQ"] == expected_ack:
                    self.seq = expected_ack
                    return

            except socket.timeout:
                print("[SEND] Timeout. Retransmitiendo segmento...")

    def send(self, message):
        if isinstance(message, str):
            message = message.encode()

        message_length = len(message)
        length_payload = str(message_length).encode()

        print(f"[SEND] Enviando largo del mensaje: {message_length}")

        # Primer segmento: largo del mensaje.
        self._send_with_stop_and_wait(length_payload)

        # Segmentos siguientes: contenido real.
        for i in range(0, message_length, MAX_DATA_SIZE):
            chunk = message[i:i + MAX_DATA_SIZE]
            self._send_with_stop_and_wait(chunk)

    def _receive_next_data_segment(self):
        while True:
            try:
                segment, sender_address = self._recvfrom_or_pending()
                parsed = self.parse_segment(segment)

                seq = parsed["SEQ"]
                data = parsed["DATA"]

                print(
                    f"[RECV] Recibido segmento seq={seq}, "
                    f"esperado={self.expected_seq}, data={data!r}"
                )

                self.destination_address = sender_address

                # Segmento esperado.
                if seq == self.expected_seq:
                    self.expected_seq += len(data)
                    self._send_ack(self.expected_seq)

                    print(f"[RECV] ACK enviado con seq={self.expected_seq}")

                    return data

                # Segmento duplicado.
                elif seq < self.expected_seq:
                    print("[RECV] Segmento duplicado. Reenviando ACK.")
                    self._send_ack(self.expected_seq)

                # Segmento fuera de orden.
                else:
                    print("[RECV] Segmento fuera de orden. Reenviando último ACK.")
                    self._send_ack(self.expected_seq)

            except socket.timeout:
                continue

    def recv(self, buff_size):
        result = b""

        # Primero consumir datos pendientes de llamadas anteriores.
        if self.pending_data:
            amount = min(buff_size, len(self.pending_data))
            result += self.pending_data[:amount]
            self.pending_data = self.pending_data[amount:]
            self.remaining_message_length -= amount

            if len(result) == buff_size or self.remaining_message_length == 0:
                return result

        # Si no hay mensaje en curso, primero recibimos el largo.
        if self.remaining_message_length == 0:
            length_data = self._receive_next_data_segment()
            self.remaining_message_length = int(length_data.decode())

            print(f"[RECV] Largo del mensaje recibido: {self.remaining_message_length}")

        # Recibir datos hasta llenar buff_size o terminar mensaje.
        while len(result) < buff_size and self.remaining_message_length > 0:
            data = self._receive_next_data_segment()

            available_space = buff_size - len(result)

            if len(data) <= available_space:
                result += data
                self.remaining_message_length -= len(data)
            else:
                result += data[:available_space]
                self.pending_data += data[available_space:]
                self.remaining_message_length -= available_space

        return result

    def close(self):
        """
        Cierra la conexión desde el lado Host A tolerando pérdidas.

        Secuencia:
        1. Envía FIN.
        2. Espera ACK y FIN.
        3. Si hay timeout, reenvía FIN hasta 3 veces.
        4. Si recibe ACK y FIN, envía el último ACK tres veces.
        5. Cierra el socket.
        """

        fin_segment = self.create_segment(
            syn=0,
            ack=0,
            fin=1,
            seq=self.seq,
            data=b""
        )

        got_ack = False
        got_fin = False
        timeout_count = 0

        print(f"[CLOSE] Enviando FIN seq={self.seq}")
        self._sendto(fin_segment, self.destination_address)

        while not (got_ack and got_fin):
            try:
                response, sender_address = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(response)

                print(
                    f"[CLOSE] Recibido: "
                    f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                    f"FIN={parsed['FIN']} SEQ={parsed['SEQ']} "
                    f"desde {sender_address}"
                )

                if parsed["ACK"] == 1:
                    got_ack = True
                    print("[CLOSE] ACK del FIN recibido")

                if parsed["FIN"] == 1:
                    got_fin = True
                    print("[CLOSE] FIN de la contraparte recibido")

            except socket.timeout:
                timeout_count += 1

                print(
                    f"[CLOSE] Timeout esperando ACK/FIN "
                    f"({timeout_count}/3). Reenviando FIN..."
                )

                if timeout_count >= 3:
                    print("[CLOSE] Se alcanzaron 3 timeouts. Se asume contraparte cerrada.")
                    self.udp_socket.close()
                    return

                self._sendto(fin_segment, self.destination_address)

        # Si recibió ACK y FIN con éxito, envía ACK final tres veces.
        final_ack_segment = self.create_segment(
            syn=0,
            ack=1,
            fin=0,
            seq=self.seq + 1,
            data=b""
        )

        for i in range(3):
            print(f"[CLOSE] Enviando ACK final {i + 1}/3 seq={self.seq + 1}")
            self._sendto(final_ack_segment, self.destination_address)
            time.sleep(TIMEOUT)

        print("[CLOSE] Cerrando socket")
        self.udp_socket.close()

    def recv_close(self):
        """
        Cierra la conexión desde el lado Host B tolerando pérdidas.

        Secuencia:
        1. Espera FIN.
        2. Envía ACK.
        3. Envía FIN.
        4. Espera ACK final hasta 3 timeouts.
        5. Si no llega ACK final, asume que la contraparte cerró.
        6. Cierra el socket.
        """

        print("[RECV_CLOSE] Esperando FIN...")

        # Paso 1: esperar FIN
        while True:
            try:
                segment, sender_address = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(segment)

                print(
                    f"[RECV_CLOSE] Recibido: "
                    f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                    f"FIN={parsed['FIN']} SEQ={parsed['SEQ']} "
                    f"desde {sender_address}"
                )

                self.destination_address = sender_address

                if parsed["FIN"] == 1:
                    print("[RECV_CLOSE] FIN recibido")
                    break

            except socket.timeout:
                continue

        # Paso 2: enviar ACK del FIN recibido
        ack_segment = self.create_segment(
            syn=0,
            ack=1,
            fin=0,
            seq=self.seq,
            data=b""
        )

        print(f"[RECV_CLOSE] Enviando ACK seq={self.seq}")
        self._sendto(ack_segment, self.destination_address)

        # Paso 3: enviar FIN propio
        fin_segment = self.create_segment(
            syn=0,
            ack=0,
            fin=1,
            seq=self.seq,
            data=b""
        )

        print(f"[RECV_CLOSE] Enviando FIN seq={self.seq}")
        self._sendto(fin_segment, self.destination_address)

        # Paso 4: esperar ACK final hasta 3 timeouts
        timeout_count = 0

        while True:
            try:
                response, sender_address = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(response)

                print(
                    f"[RECV_CLOSE] Recibido: "
                    f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                    f"FIN={parsed['FIN']} SEQ={parsed['SEQ']} "
                    f"desde {sender_address}"
                )

                if parsed["ACK"] == 1:
                    print("[RECV_CLOSE] ACK final recibido")
                    break

                # Si vuelve a llegar FIN duplicado, reenviamos ACK y FIN.
                if parsed["FIN"] == 1:
                    print("[RECV_CLOSE] FIN duplicado recibido. Reenviando ACK y FIN.")
                    self._sendto(ack_segment, self.destination_address)
                    self._sendto(fin_segment, self.destination_address)

            except socket.timeout:
                timeout_count += 1

                print(
                    f"[RECV_CLOSE] Timeout esperando ACK final "
                    f"({timeout_count}/3)"
                )

                if timeout_count >= 3:
                    print("[RECV_CLOSE] Se alcanzaron 3 timeouts. Se asume contraparte cerrada.")
                    break

        print("[RECV_CLOSE] Cerrando socket")
        self.udp_socket.close()


    