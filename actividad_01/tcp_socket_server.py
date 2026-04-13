import socket
from proxy import parse_HTTP_message, create_HTTP_message

if __name__ == "__main__":
    buffer_size = 4096
    address = ('localhost', 8000)

    print('Creando socket - Servidor')

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind(address)
    server_socket.listen(1)

    print('... Esperando cliente')

    new_socket, client_address = server_socket.accept()
    print(f'Conexión aceptada desde {client_address}')

    recv_message = new_socket.recv(buffer_size).decode()

    print('\n--- REQUEST RECIBIDO ---')
    print(recv_message)

    parsed = parse_HTTP_message(recv_message)

    print('\n--- PARSEADO ---')
    print(parsed)

    recreated = create_HTTP_message(parsed)

    print('\n--- RECONSTRUIDO ---')
    print(recreated)

    new_socket.close()
    server_socket.close()