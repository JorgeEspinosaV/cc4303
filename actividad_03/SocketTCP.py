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
    
    
    def _send_ack(self, ack_seq):
        """
        Envía un ACK a la contraparte.
        Usamos el campo SEQ del header como número de confirmación.
        """
        ack_segment = self.create_segment(
            syn=0,
            ack=1,
            fin=0,
            seq=ack_seq,
            data=b""
        )

        self.udp_socket.sendto(ack_segment, self.destination_address)

    def _send_with_stop_and_wait(self, payload):
        """
        Envía un payload usando Stop & Wait.
        Envía el segmento con self.seq y espera un ACK con seq = self.seq + len(payload).
        Si hay timeout, retransmite.
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

            self.udp_socket.sendto(segment, self.destination_address)

            try:
                response, _ = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(response)

                print(
                    f"[SEND] Recibido: ACK={parsed['ACK']} "
                    f"SEQ={parsed['SEQ']}"
                )

                if parsed["ACK"] == 1 and parsed["SEQ"] == expected_ack:
                    self.seq = expected_ack
                    return

            except socket.timeout:
                print("[SEND] Timeout. Retransmitiendo segmento...")

    def send(self, message):
        """
        Envía un mensaje usando Stop & Wait.

        Primero envía el largo total del mensaje.
        Luego envía el contenido dividido en trozos de máximo 16 bytes.
        """

        if isinstance(message, str):
            message = message.encode()

        message_length = len(message)
        length_payload = str(message_length).encode()

        print(f"[SEND] Enviando largo del mensaje: {message_length}")

        # Primer segmento: largo del mensaje
        self._send_with_stop_and_wait(length_payload)

        # Luego se envía el mensaje en trozos de máximo 16 bytes
        for i in range(0, message_length, MAX_DATA_SIZE):
            chunk = message[i:i + MAX_DATA_SIZE]
            self._send_with_stop_and_wait(chunk)

    def _receive_next_data_segment(self):
        """
        Recibe el siguiente segmento de datos esperado.
        Si llega un duplicado, vuelve a enviar ACK pero no duplica datos.
        """

        while True:
            try:
                segment, sender_address = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(segment)

                seq = parsed["SEQ"]
                data = parsed["DATA"]

                print(
                    f"[RECV] Recibido segmento seq={seq}, "
                    f"esperado={self.expected_seq}, data={data!r}"
                )

                # Aseguramos dirección de destino para responder ACK
                self.destination_address = sender_address

                # Caso normal: llegó el segmento esperado
                if seq == self.expected_seq:
                    self.expected_seq += len(data)
                    self._send_ack(self.expected_seq)

                    print(f"[RECV] ACK enviado con seq={self.expected_seq}")

                    return data

                # Caso duplicado: ya fue recibido antes
                elif seq < self.expected_seq:
                    print("[RECV] Segmento duplicado. Reenviando ACK.")
                    self._send_ack(self.expected_seq)

                # Caso fuera de orden
                else:
                    print("[RECV] Segmento fuera de orden. Reenviando último ACK.")
                    self._send_ack(self.expected_seq)

            except socket.timeout:
                # El receptor simplemente sigue esperando.
                continue

    def recv(self, buff_size):
        """
        Recibe datos usando Stop & Wait.

        Retorna a lo más buff_size bytes.
        Si el mensaje completo es más grande que buff_size, guarda los datos
        pendientes para futuras llamadas a recv().
        """

        result = b""

        # Primero consumir datos pendientes de llamadas anteriores
        if self.pending_data:
            amount = min(buff_size, len(self.pending_data))
            result += self.pending_data[:amount]
            self.pending_data = self.pending_data[amount:]
            self.remaining_message_length -= amount

            if len(result) == buff_size or self.remaining_message_length == 0:
                return result

        # Si no hay mensaje en curso, primero recibimos el largo
        if self.remaining_message_length == 0:
            length_data = self._receive_next_data_segment()
            self.remaining_message_length = int(length_data.decode())

            print(f"[RECV] Largo del mensaje recibido: {self.remaining_message_length}")

        # Recibir datos hasta llenar buff_size o terminar mensaje
        while len(result) < buff_size and self.remaining_message_length > 0:
            data = self._receive_next_data_segment()

            available_space = buff_size - len(result)

            # Si el segmento cabe completo
            if len(data) <= available_space:
                result += data
                self.remaining_message_length -= len(data)

            # Si el segmento excede buff_size, guardar sobrante
            else:
                result += data[:available_space]
                self.pending_data += data[available_space:]
                self.remaining_message_length -= available_space

        return result
    
    def close(self):
        """
        Cierra la conexión desde el lado Host A.

        Secuencia:
        1. Envía FIN.
        2. Espera ACK.
        3. Espera FIN.
        4. Envía ACK final.
        5. Cierra el socket UDP.
        """

        # Paso 1: enviar FIN
        fin_segment = self.create_segment(
            syn=0,
            ack=0,
            fin=1,
            seq=self.seq,
            data=b""
        )

        print(f"[CLOSE] Enviando FIN seq={self.seq}")
        self.udp_socket.sendto(fin_segment, self.destination_address)

        # Paso 2: esperar ACK del FIN
        while True:
            response, _ = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
            parsed = self.parse_segment(response)

            print(
                f"[CLOSE] Recibido: "
                f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                f"FIN={parsed['FIN']} SEQ={parsed['SEQ']}"
            )

            if parsed["ACK"] == 1:
                print("[CLOSE] ACK recibido")
                break

        # Paso 3: esperar FIN de la contraparte
        while True:
            response, _ = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
            parsed = self.parse_segment(response)

            print(
                f"[CLOSE] Recibido: "
                f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                f"FIN={parsed['FIN']} SEQ={parsed['SEQ']}"
            )

            if parsed["FIN"] == 1:
                print("[CLOSE] FIN recibido desde contraparte")

                # Paso 4: enviar ACK final
                ack_segment = self.create_segment(
                    syn=0,
                    ack=1,
                    fin=0,
                    seq=self.seq + 1,
                    data=b""
                )

                print(f"[CLOSE] Enviando ACK final seq={self.seq + 1}")
                self.udp_socket.sendto(ack_segment, self.destination_address)
                break

        print("[CLOSE] Cerrando socket")
        self.udp_socket.close()

    def recv_close(self):
        """
        Cierra la conexión desde el lado Host B.

        Secuencia:
        1. Espera FIN.
        2. Envía ACK.
        3. Envía FIN.
        4. Espera ACK final.
        5. Cierra el socket UDP.
        """

        print("[RECV_CLOSE] Esperando FIN...")

        # Paso 1: esperar FIN desde Host A
        while True:
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

        # Paso 2: enviar ACK al FIN recibido
        ack_segment = self.create_segment(
            syn=0,
            ack=1,
            fin=0,
            seq=self.seq,
            data=b""
        )

        print(f"[RECV_CLOSE] Enviando ACK seq={self.seq}")
        self.udp_socket.sendto(ack_segment, self.destination_address)

        # Paso 3: enviar FIN propio
        fin_segment = self.create_segment(
            syn=0,
            ack=0,
            fin=1,
            seq=self.seq,
            data=b""
        )

        print(f"[RECV_CLOSE] Enviando FIN seq={self.seq}")
        self.udp_socket.sendto(fin_segment, self.destination_address)

        # Paso 4: esperar ACK final
        while True:
            response, _ = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
            parsed = self.parse_segment(response)

            print(
                f"[RECV_CLOSE] Recibido: "
                f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                f"FIN={parsed['FIN']} SEQ={parsed['SEQ']}"
            )

            if parsed["ACK"] == 1:
                print("[RECV_CLOSE] ACK final recibido")
                break

        print("[RECV_CLOSE] Cerrando socket")
        self.udp_socket.close()