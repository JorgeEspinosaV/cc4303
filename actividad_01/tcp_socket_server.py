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
    campos_requeridos = ["nombre"]
    for campo in campos_requeridos:
        if campo not in config:
            raise SystemExit(f"Error: falta el campo '{campo}' en el JSON")
        if not isinstance(config[campo], str) or not config[campo].strip():
            raise SystemExit(f"Error: el campo '{campo}' debe ser un string no vacío")

    return config

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise SystemExit(f"Uso: python {sys.argv[0]} <archivo_config.json>")
    
    config = cargar_config(sys.argv[1])
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buffer_size = 4096
    new_socket_address = ('localhost', 8000)

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
                    recv_message = new_socket.recv(buffer_size).decode()
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

                    # Creamos socket cliente
                    print('Creando socket - Cliente')
                     
                    # armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
                    # socket.SOCK_STREAM = socket orientado a conexión
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                     
                    # Como es un socket orientado a conexión debemos conectarlo a la dirección acordada
                    client_socket.connect(address)
                      
                    client_socket.send(send_message)

                except Exception as e:
                    print(f'Error al manejar la petición: {e}')

                finally:
                    new_socket.close()  # cierra socket cliente

            except Exception as e:
                print(f'Error al aceptar conexión: {e}')

    except KeyboardInterrupt:
        print('\nServidor detenido por el usuario')

    finally:
        server_socket.close()  # cierra socket servidor
        print('Socket del servidor cerrado')
