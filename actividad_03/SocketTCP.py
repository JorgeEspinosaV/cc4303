import socket
import random
import time 
#largo de bytes
MAX_DATA_SIZE = 16
#Tamaño maximo de socket UDP
UDP_BUFFER_SIZE = 1024
#tiempo de espera
TIMEOUT = 1.0

# Simular pérdida
# 0.2 = 20% de pérdida
LOSS_PROBABILITY = 0.2
#cuando se pierde un paquete
DEBUG_LOSS = True


class SocketTCP:
    def __init__(self):
        #Socket UDP interno
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #Timeout
        self.udp_socket.settimeout(TIMEOUT)

        #Guarda direccion local del socket
        self.origin_address = None
        #Guarda direccion de destino del socket
        self.destination_address = None

        #numero de secuencia inicial aleatorio
        self.seq = random.randint(0, 100)
        #Numero de secuencia que esperamos recibir
        self.expected_seq = None
        #Guarda los bytes sobrantes 
        # cuando recv recibe mas de lo que puede retornar
        self.pending_data = b""
        #Guarda cuantos bytes faltan por entregar en el mensaje
        self.remaining_message_length = 0

        # Segmentos que llegaron antes de tiempo.
        # Cuando el ultimo ACK se perdió en el handshake.
        self.pending_segments = []

    #funciones estáticas
    @staticmethod
    #Crea segmentos a partir de Headers TCP
    def create_segment(syn, ack, fin, seq, data=b""):
        #Si vienen los datos como texto normal
        if isinstance(data, str):
            #los pasamos a bytes
            data = data.encode()

        #Construimos el header
        header = f"{int(syn)}|||{int(ack)}|||{int(fin)}|||{int(seq)}|||".encode()
        #une el header con los datos
        return header + data

    @staticmethod
    #Recibe segmento en bytes y los separa en sus partes
    def parse_segment(segment):
        parts = segment.split(b"|||", 4)

        #Convierte las partes del header a enteros
        syn = int(parts[0].decode())
        ack = int(parts[1].decode())
        fin = int(parts[2].decode())
        seq = int(parts[3].decode())
        data = parts[4]

        #Devuelve el diccionario
        return {
            "SYN": syn,
            "ACK": ack,
            "FIN": fin,
            "SEQ": seq,
            "DATA": data,
        }

    #Envía un segmento pero puede simular pérdida manual
    def _sendto(self, segment, address):
        

        #Genera un número aleatorio entre 0 y 1, si es menor que Loss_probability se pierde
        if LOSS_PROBABILITY > 0 and random.random() < LOSS_PROBABILITY:
            #Debug para manejos de perdidas
            if DEBUG_LOSS:
                print(f"[LOSS] Paquete perdido artificialmente hacia {address}: {segment!r}")
            return 0

        return self.udp_socket.sendto(segment, address)

    #Entrega segmentos guardados, sino hay segmentos pedientes lee desde el socket UDP
    def _recvfrom_or_pending(self):

        #Si hay segmentos pendientes
        if self.pending_segments:
            #Devuelve el primero
            return self.pending_segments.pop(0)

        #Si no hay pendientes, lee normalmente el socket UDP
        return self.udp_socket.recvfrom(UDP_BUFFER_SIZE)

    #Asocia el socket a una direccion local
    def bind(self, address):
        #Guarda la dirección local
        self.origin_address = address
        #Hace que el socket UDP escuche en esa direccion
        self.udp_socket.bind(address)

    #Lado cliente del 3 way handshake, maneja perdida de SYN y SYN-ACK mediante retransmisión
    def connect(self, address):

        #Guarda direccion del servidor principal
        self.destination_address = address

        #Crea segmento SYN
        syn_segment = self.create_segment(
            syn=1,
            ack=0,
            fin=0,
            seq=self.seq,
            data=b""
        )

        #Bucle hasta que se complete el handshake.
        #si hay perdida reintenta
        while True:
            #Debug
            print(f"[CLIENTE] Enviando SYN seq={self.seq}")
            #Envía el SYN
            self._sendto(syn_segment, self.destination_address)

            #Inteta recibir respuesta
            try:
                #espera recibir SYN-ACK
                #sino llega en timeout saca socket timeout
                response, server_address = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                #parsea la respuesta
                parsed = self.parse_segment(response)

                print(
                    f"[CLIENTE] Recibido: "
                    f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                    f"FIN={parsed['FIN']} SEQ={parsed['SEQ']} "
                    f"desde {server_address}"
                )

                if parsed["SYN"] == 1 and parsed["ACK"] == 1:
                    # Actualiza el nuevo socket del servidor
                    self.destination_address = server_address
                    #Guarda que secuencia espera recibir del servidor despues
                    self.expected_seq = parsed["SEQ"] + 1

                    #Avanza la secuencia del cliente despues del SYN
                    self.seq += 1

                    #Crea el ack final del handshake
                    ack_segment = self.create_segment(
                        syn=0,
                        ack=1,
                        fin=0,
                        seq=self.seq,
                        data=b""
                    )

                    print(f"[CLIENTE] Enviando ACK final seq={self.seq}")
                    #Envia el ack final
                    self._sendto(ack_segment, self.destination_address)

                    print("[CLIENTE] Handshake completado")
                    return
                
                #Termina connect


            #Sino llego a SYN-ACK vuelve al inicio del while y reenvia syn 
            except socket.timeout:
                print("[CLIENTE] Timeout esperando SYN-ACK. Reintentando handshake...")

    #Lado servidor del 3-way handshake.
    
    #Espera una conexión entrante
    def accept(self):

        print("[SERVIDOR] Esperando SYN...")

        #Espera indefinidamente conexiones
        while True:
            try:
                #Espera recibir un segmento en socket principal 
                segment, client_address = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                #Parsea el segmento
                parsed = self.parse_segment(segment)

                print(
                    f"[SERVIDOR] Recibido: "
                    f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                    f"FIN={parsed['FIN']} SEQ={parsed['SEQ']} "
                    f"desde {client_address}"
                )

                #Si es un SYN inicia handshake
                if parsed["SYN"] == 1:
                    #Crea un nuevo socketTCP pra esta conexión 
                    connection_socket = SocketTCP()
                    #Conecta el nuevo socket a un puerto libre
                    connection_socket.bind(("127.0.0.1", 0))

                    #Obtiene la direccion real del socket
                    new_address = connection_socket.udp_socket.getsockname()

                    #Socket sabe a que cliente responder
                    connection_socket.destination_address = client_address
                    #Siguiente a esperar
                    connection_socket.expected_seq = parsed["SEQ"] + 1

                    #Crea el SYN-ACK
                    syn_ack_segment = connection_socket.create_segment(
                        syn=1,
                        ack=1,
                        fin=0,
                        seq=connection_socket.seq,
                        data=b""
                    )

                    #Bucle si se pierde el ACK final
                    while True:
                        print(
                            f"[SERVIDOR] Enviando SYN-ACK seq={connection_socket.seq} "
                            f"desde {new_address}"
                        )

                        #Envia SYN-ACK desde el nuevo socket
                        connection_socket._sendto(
                            syn_ack_segment,
                            client_address
                        )

                        try:
                            #Espera ACK final, osino recibe data si ACK se perdió
                            response, response_address = connection_socket._recvfrom_or_pending()
                            #parsea lo recibido
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

                            #llegó ACK final.
                            if parsed_response["ACK"] == 1:
                                #Avanza la secuencia
                                connection_socket.seq += 1

                                print("[SERVIDOR] Handshake completado")
                                return connection_socket, new_address

                            #se perdió ACK final, pero llegó DATA.
                            elif (
                                parsed_response["SYN"] == 0
                                and parsed_response["ACK"] == 0
                                and parsed_response["FIN"] == 0
                                and parsed_response["SEQ"] == connection_socket.expected_seq
                            ):
                                print("[SERVIDOR] Llegaron datos antes del ACK final.")
                                print("[SERVIDOR] Se asume que el ACK final del handshake se perdió.")
                                print("[SERVIDOR] Guardando primer segmento para recv().")

                                #Guarda ese primer data para que recv no lo pierde
                                connection_socket.pending_segments.append(
                                    (response, response_address)
                                )

                                connection_socket.seq += 1

                                print("[SERVIDOR] Handshake completado por llegada de datos")
                                return connection_socket, new_address

                        #sino llega ACK final, el servidor reenvia SYN-ACK
                        except socket.timeout:
                            print("[SERVIDOR] Timeout esperando ACK final. Reenviando SYN-ACK...")

            except socket.timeout:
                continue

    #Envia ACK
    def _send_ack(self, ack_seq):
        #crea un ack
        ack_segment = self.create_segment(
            syn=0,
            ack=1,
            fin=0,
            seq=ack_seq,
            data=b""
        )

        #Envia el ACK
        self._sendto(ack_segment, self.destination_address)

    #Envia un payload usando stop & wait, envia el segmento y espera ACK
    #Si no llega ACK por timeout, retransmite
    def _send_with_stop_and_wait(self, payload):
    
        #Calcula el ack que espera
        expected_ack = self.seq + len(payload)

        #Crea segmento de datos
        segment = self.create_segment(
            syn=0,
            ack=0,
            fin=0,
            seq=self.seq,
            data=payload
        )

        #Repite hasta recibir el ACK correcto 
        while True:
            print(
                f"[SEND] Enviando segmento seq={self.seq}, "
                f"esperando ACK={expected_ack}, data={payload!r}"
            )

            #Envia el segmento
            self._sendto(segment, self.destination_address)

            try:
                #Espera ACK
                response, sender_address = self._recvfrom_or_pending()
                #Parsea lo recibido
                parsed = self.parse_segment(response)

                print(
                    f"[SEND] Recibido: "
                    f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                    f"FIN={parsed['FIN']} SEQ={parsed['SEQ']}"
                )

                #Al cliente le llega SYN-ACK duplicado porque
                # se perdió el ACK final del handshake.
                if parsed["SYN"] == 1 and parsed["ACK"] == 1:
                    print("[SEND] SYN-ACK duplicado recibido. Reenviando ACK final.")

                    #Recrea el ack final
                    ack_segment = self.create_segment(
                        syn=0,
                        ack=1,
                        fin=0,
                        seq=self.seq,
                        data=b""
                    )

                    #Reenvia ACK final
                    self._sendto(ack_segment, sender_address)
                    # y sigue esperando ACK data
                    continue

                #Si ACK fue correcto entonces el segmento fue recibido 
                if parsed["ACK"] == 1 and parsed["SEQ"] == expected_ack:
                    #avanza en la secuencia
                    self.seq = expected_ack
                    return

            #Sino llega ACK retransmite el mismo segmento
            except socket.timeout:
                print("[SEND] Timeout. Retransmitiendo segmento...")

    #Envia mensaje completo
    def send(self, message):
        #convierte texto a bytes si es necesario
        if isinstance(message, str):
            message = message.encode()

        #calcula largo total del mensaje
        message_length = len(message)
        #Convierte el largo a bytes
        length_payload = str(message_length).encode()

        print(f"[SEND] Enviando largo del mensaje: {message_length}")

        # Envia el largo del mensaje.
        self._send_with_stop_and_wait(length_payload)

        #Recorre el mensaje
        for i in range(0, message_length, MAX_DATA_SIZE):
            #Extrae un trozo de a lo mas 16 bytes 
            chunk = message[i:i + MAX_DATA_SIZE]
            #Envia ese trozo
            self._send_with_stop_and_wait(chunk)

    #recv(uff_size) y stop & wait lado receptor
    def _receive_next_data_segment(self):
        while True:
            try:
                #Lee un segmento, ya sea del socket o de los pendientes
                segment, sender_address = self._recvfrom_or_pending()
                #Parsea
                parsed = self.parse_segment(segment)

                #Saca numero de secuencia y datos
                seq = parsed["SEQ"]
                data = parsed["DATA"]

                print(
                    f"[RECV] Recibido segmento seq={seq}, "
                    f"esperado={self.expected_seq}, data={data!r}"
                )

                #Actualiza a quien debe responder ACK
                self.destination_address = sender_address

                # Segmento esperado
                if seq == self.expected_seq:
                    self.expected_seq += len(data)
                    #Envia ACK
                    self._send_ack(self.expected_seq)

                    print(f"[RECV] ACK enviado con seq={self.expected_seq}")

                    return data

                # Segmento duplicado
                elif seq < self.expected_seq:
                    print("[RECV] Segmento duplicado. Reenviando ACK.")
                    #Reenvia el ultimo ACK
                    self._send_ack(self.expected_seq)

                # Segmento fuera de orden
                else:
                    print("[RECV] Segmento fuera de orden. Reenviando último ACK.")
                    #Reenvia el ultimo ACK conocido
                    self._send_ack(self.expected_seq)

            #sino llega sigo esperando
            except socket.timeout:
                continue

    #Funcion para recibir datos
    def recv(self, buff_size):
        #Acumulamos lo que devolvera la llamada
        result = b""

        #consumir datos pendientes de llamadas anteriores
        if self.pending_data:
            #Calcula cuanto puede devolver
            amount = min(buff_size, len(self.pending_data))
            #Lo agrega al resultado
            result += self.pending_data[:amount]
            #Elimina lo que ya entrego
            self.pending_data = self.pending_data[amount:]
            #Actualiza cuantos bytes quedan pendientes
            self.remaining_message_length -= amount

            #Si ya lleno el buffer o no queda nada, retorna
            if len(result) == buff_size or self.remaining_message_length == 0:
                return result

        #Si no hay mensaje en curso, primero recibimos el largo
        if self.remaining_message_length == 0:
            #Recibe el segmento que contiene el largo
            length_data = self._receive_next_data_segment()
            #El largo lo convierte en entero
            self.remaining_message_length = int(length_data.decode())

            print(f"[RECV] Largo del mensaje recibido: {self.remaining_message_length}")

        # Recibir datos hasta llenar buff_size o terminar mensaje
        while len(result) < buff_size and self.remaining_message_length > 0:
            #Recibe el siguiente segmentos de datos
            data = self._receive_next_data_segment()

            #Calcula cuanto espacio queda en el resultado
            available_space = buff_size - len(result)

            #Si cabe el segmento
            if len(data) <= available_space:
                #Agrega completamente
                result += data
                self.remaining_message_length -= len(data)
            else:
                #Agrega lo que cabe
                result += data[:available_space]
                 #Guarda lo sobrante
                self.pending_data += data[available_space:]
                #Actualiza lo pendiente
                self.remaining_message_length -= available_space

        return result

    #Cierra la conexión desde el lado Host A tolerando perdidas
    def close(self):

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
        #Envia FIN
        self._sendto(fin_segment, self.destination_address)

        #Espera hasta recibir ACK y FIN
        while not (got_ack and got_fin):
            try:
                #Espera respuesta
                response, sender_address = self.udp_socket.recvfrom(UDP_BUFFER_SIZE)
                parsed = self.parse_segment(response)

                print(
                    f"[CLOSE] Recibido: "
                    f"SYN={parsed['SYN']} ACK={parsed['ACK']} "
                    f"FIN={parsed['FIN']} SEQ={parsed['SEQ']} "
                    f"desde {sender_address}"
                )

                if parsed["ACK"] == 1:
                    #Marca que llego ACK
                    got_ack = True
                    print("[CLOSE] ACK del FIN recibido")

                if parsed["FIN"] == 1:
                    #Marca que llego FIN
                    got_fin = True
                    print("[CLOSE] FIN de la contraparte recibido")

            #Sino llega nada marca timeout
            except socket.timeout:
                timeout_count += 1

                print(
                    f"[CLOSE] Timeout esperando ACK/FIN "
                    f"({timeout_count}/3). Reenviando FIN..."
                )

                #Si hay 3 timeout o mas asime que la contraparte cerro
                if timeout_count >= 3:
                    print("[CLOSE] Se alcanzaron 3 timeouts. Se asume contraparte cerrada.")
                    #Cierra
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

        #Envia ACK final 3 veces
        for i in range(3):
            print(f"[CLOSE] Enviando ACK final {i + 1}/3 seq={self.seq + 1}")
            self._sendto(final_ack_segment, self.destination_address)
            #Espera un timeout entre cada envio
            time.sleep(TIMEOUT)

        print("[CLOSE] Cerrando socket")
        #Cierra el socket
        self.udp_socket.close()

    #Cierra la conexión desde el lado Host B tolerando perdidas
    def recv_close(self):

        print("[RECV_CLOSE] Esperando FIN...")

        #esperar FIN
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

        #enviar ACK del FIN recibido
        ack_segment = self.create_segment(
            syn=0,
            ack=1,
            fin=0,
            seq=self.seq,
            data=b""
        )

        print(f"[RECV_CLOSE] Enviando ACK seq={self.seq}")
        self._sendto(ack_segment, self.destination_address)

        #enviar FIN propio
        fin_segment = self.create_segment(
            syn=0,
            ack=0,
            fin=1,
            seq=self.seq,
            data=b""
        )

        print(f"[RECV_CLOSE] Enviando FIN seq={self.seq}")
        self._sendto(fin_segment, self.destination_address)

        #esperar ACK final hasta 3 timeouts
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


    