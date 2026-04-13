import socket
from proxy import parse_HTTP_message, create_HTTP_message

if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buffer_size = 4096
    new_socket_address = ('localhost', 8000)

    print('Creando socket - Servidor')
     # armamos el socket
     # los parámetros que recibe el socket indican el tipo de conexión
     # socket.SOCK_STREAM = socket orientado a conexión
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # le indicamos al server socket que debe atender peticiones en la dirección address
    # para ello usamos bind
    server_socket.bind(new_socket_address)
     # luego con listen (función de sockets de python) le decimos que puede
     # tener hasta 3 peticiones de conexión encoladas
     # si recibiera una 4ta petición de conexión la va a rechazar
    server_socket.listen(3)
    # nos quedamos esperando a que llegue una petición de conexión

    print('... Esperando cliente')
    # cuando llega una petición de conexión la aceptamos
    # y se crea un nuevo socket que se comunicará con el cliente
    new_socket, client_address = server_socket.accept()
    print(f'Conexión aceptada desde {client_address}')

    recv_message = new_socket.recv(buffer_size).decode()

    print('\n--- REQUEST RECIBIDO ---')
    print(recv_message)

    parsed = parse_HTTP_message(recv_message)

    print('\n--- PARSEADO ---')
    print(parsed)

    recreated = create_HTTP_message(parsed)

    # response o respuesta HTTP a la petición que se esta recibiendo
    html = """<html>
    <head>
        <p>Servidor HTTP</p>
    </head>
    <body>
        <p>Hello, this is a very simple HTML document.</p>
    </body>
</html>"""

    response = {
        "start_line": "HTTP/1.1 200 OK",
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": str(len(html.encode("utf-8"))),
            "Connection": "close"
        },
        "body": html
    }

    response_message = create_HTTP_message(response)

    print('\n--- RESPONSE ENVIADO ---')
    print(response_message)

    new_socket.sendall(response_message.encode("utf-8"))



    

    new_socket.close()
    server_socket.close()