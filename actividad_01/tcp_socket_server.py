import socket
from proxy import parse_HTTP_message, create_HTTP_message
import json

def cargar_config(path: str) -> dict:
    try:
        with open(path) as f:
            config = json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"Error: no se encontró el archivo '{path}'")
    except json.JSONDecodeError as e:
        raise SystemExit(f"Error: JSON malformado en '{path}': {e}")

    # Validar campos requeridos
    campos_requeridos = ["user", "blocked"]
    for campo in campos_requeridos:
        if campo not in config:
            raise SystemExit(f"Error: falta el campo '{campo}' en el JSON")

    return config

def obtener_target_host(headers: dict) -> tuple[str, int]:
    host = headers.get("Host") or headers.get("host", "")
    if not host:
        raise ValueError("No se encontró 'Host' en el header")
    if ":" in host:
        hostname, port_str = host.rsplit(":", 1)
        port = int(port_str)
    else:
        hostname = host 
        port = 80
    return hostname, port

def esta_bloqueado(full_url: str, blocked_list: list) -> bool:
    full_url = full_url.lower()
    for blocked in blocked_list:
        if blocked.lower() in full_url:
            return True
    return False

def replace_content(body: str, forbidden_words: list[dict[str, str]]) -> str:
    for i in forbidden_words:
        for key, value in i.items():
            body = body.replace(key, value)

    return body

def recv_full_message(sock, buffer_size=50):
    data = b""
    
    # recibimos hasta encontrar el fin de headers
    while b"\r\n\r\n" not in data:
        chunk = sock.recv(buffer_size)
        if not chunk:
            break
        data += chunk
    
    # Separamos headers y lo que haya llegado del body
    header_part, _, body_part = data.partition(b"\r\n\r\n")
    
    # Buscamos content-length en los headers
    content_length = 0
    for line in header_part.decode().split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":")[1].strip())
            break
    
    # Seguimos leyendo el body hasta completarlo
    while len(body_part) < content_length:
        chunk = sock.recv(buffer_size)
        if not chunk:
            break
        body_part += chunk
    
    return (header_part + b"\r\n\r\n" + body_part).decode()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise SystemExit(f"Uso: python {sys.argv[0]} <archivo_config.json>")
    
    config = cargar_config(sys.argv[1])
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buffer_size = 4096
    new_socket_address = ('0.0.0.0', 8000)

    print('Creando socket - Servidor')
    # Obtenemos el archivo de config 


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
    print('... Esperando clientes (Ctrl+C para detener)')

    try:
        while True:  # acepta conexiones indefinidamente
            try:
                new_socket, client_address = server_socket.accept()
                print(f'\nConexión aceptada desde {client_address}')

                try:
                    recv_message = recv_full_message(new_socket, buffer_size)
                    if not recv_message:
                        continue

                    print('\n--- REQUEST RECIBIDO ---')
                    print(recv_message)
                    parsed = parse_HTTP_message(recv_message)
                    print('\n--- PARSEADO ---')
                    print(parsed)

                    html = """
                    <html>
                        <head><p>Servidor HTTP</p></head>
                        <body>
                            <p>Hello, this is a very simple HTML document.</p>
                        </body>
                    </html>
                    """
                    response = {
                        "start_line": parsed["start_line"],
                        "headers": parsed["headers"],
                        "body": parsed["body"]
                    }
                    response_message = create_HTTP_message(response)
                    print('\n--- RESPONSE ENVIADO ---')
                    print(response_message)

                    # obtenemos el host
                    hostname, port = obtener_target_host(response["headers"])

                    # verificamos si el host está bloqueado
                    if esta_bloqueado(parsed["start_line"].split(" ")[1], config["blocked"]):
                        print(f"--- BLOQUEADO: {hostname} ---")
                        body = """
                        <html>
                            <body>
                                <h1>403 Forbidden</h1>
                                <p>Este sitio está bloqueado.</p>
                            </body>
                        </html>
                        """
                        response_403 = (
                            "HTTP/1.1 403 Forbidden\r\n"
                            f"Content-Length: {len(body)}\r\n"
                            "Content-Type: text/html\r\n"
                            "Connection: close\r\n\r\n"
                            + body
                        )
                        new_socket.send(response_403.encode())
                        continue
                    # Agregamos el header a la request 
                    response["headers"]["X-ElQuePregunta"] = config["user"]
                    # Censuramos contenido
                    response_message = create_HTTP_message(response)

                    # Creamos socket cliente
                    print('Creando socket - Cliente')

                    # armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
                    # socket.SOCK_STREAM = socket orientado a conexión
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    # Como es un socket orientado a conexión debemos conectarlo a la dirección acordada
                    client_socket.connect((hostname, port))

                    print("Enviando mensaje a servidor: ", response_message)

                    client_socket.send(response_message.encode())

                    decoded_message = recv_full_message(client_socket, buffer_size)
                    # Parseamos el mensaje 
                    parsed_message = parse_HTTP_message(decoded_message)
                    parsed_message["body"] = replace_content(parsed_message["body"], config["forbidden_words"])
                    # actualizamos content-length con el nuevo tamaño del body
                    parsed_message["headers"]["Content-Length"] = str(len(parsed_message["body"].encode()))
                    new_response = create_HTTP_message(parsed_message)

                    # cerramos la conexión
                    client_socket.close()
                    
                    new_socket.send(new_response.encode())
                     

                except Exception as e:
                    print(f'Error al manejar la petición: {e}')

                finally:
                    new_socket.close()  # cierra socket cliente

            except Exception as e:
                import traceback
                print(f'Error al manejar la petición: {e}')
                traceback.print_exc()

    except KeyboardInterrupt:
        print('\nServidor detenido por el usuario')

    finally:
        server_socket.close()  # cierra socket servidor
        print('Socket del servidor cerrado')
