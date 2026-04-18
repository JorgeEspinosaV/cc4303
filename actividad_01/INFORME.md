# Informe: Construcción de un Proxy

## Información estudiantes


| Estudiante | Email  |
|------------|-------|
| Esperanza Cares | esperanza.cares@ug.uchile.cl |
| Jorge Espinosa | jorge.espinosa@ug.uchile.cl |

---


## 1. Diseño del Proxy

### 1.1 Diagrama de funcionamiento




```Mermaid
sequenceDiagram
    autonumber
    actor Cliente as Cliente (Browser / cURL)
    participant Proxy as Proxy (Tu código en la VM)
    participant Servidor as Servidor Destino (ej: cc4303)

    Note over Proxy: Socket 1: "Listen Socket"<br/>(Escuchando en IP_VM:8000)
    
    Cliente->>Proxy: Intenta conectar
    Note over Proxy: Proxy hace accept() y crea<br/>Socket 2: "Client Socket"
    
    Cliente->>Proxy: Envía HTTP Request
    
    Proxy->>Proxy: Parsea Request y revisa URI (JSON)
    
    alt URI está bloqueada (403)
        Proxy-->>Cliente: Responde HTTP 403 Forbidden + HTML (Gatos)
        Note over Proxy, Cliente: Se cierra el "Client Socket"
    else URI permitida
        Proxy->>Proxy: Modifica Headers (Agrega X-ElQuePregunta)
        
        Note over Proxy: Proxy crea<br/>Socket 3: "Server Socket"
        Proxy->>Servidor: Conecta al puerto 80 del Servidor
        
        Proxy->>Servidor: Reenvía HTTP Request modificado
        Servidor-->>Proxy: Responde HTTP Response
        
        Proxy->>Proxy: Lee el Body, busca y reemplaza forbidden_words
        
        Proxy-->>Cliente: Reenvía HTTP Response modificado
        Note over Cliente, Servidor: Se cierran "Client Socket" y "Server Socket"
    end modificado
        Note over Cliente, Servidor: Se cierran "Client Socket" y "Server Socket"
    end
```

### 1.2 Explicación del diagrama

[Explicación breve del flujo de funcionamiento del proxy]

### 1.3 Sockets necesarios

- Cantidad de sockets: [X]
- Descripción:
  - Socket 1: [Descripción]
  - Socket 2: [Descripción]
  - [Agregar más si es necesario]

---

## 2. Parte 1: Servidor HTTP

### 2.1 Función `parse_HTTP_message`

**Información extraída del mensaje HTTP:**

- [Campo 1]
- [Campo 2]
- [Campo 3]
- [Agregar campos según implementación]

**Implementación:**

```python
# Código de la función parse_HTTP_message
def parse_HTTP_message(http_message):
    # Tu implementación aquí
    pass
```

**Decisiones de diseño:**

- [Decisión 1]
- [Decisión 2]

### 2.2 Función `create_HTTP_message`

**Implementación:**

```python
# Código de la función create_HTTP_message
def create_HTTP_message(parsed_data):
    # Tu implementación aquí
    pass
```

**Decisiones de diseño:**

- [Decisión 1]
- [Decisión 2]

### 2.3 Lectura de archivos JSON

**Implementación:**

```python
# Código para leer archivos JSON
# Tu implementación aquí
```

**Decisiones de diseño:**

- [Decisión 1]
- [Decisión 2]

---

## 3. Parte 2: Implementación del Proxy

### 3.1 Transferencia de mensajes (sin modificación)

**Implementación:**

```python
import socket
from types import new_class
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

                    # obtenemos el host
                    hostname, port = obtener_target_host(response["headers"])

                    # Creamos socket cliente
                    print('Creando socket - Cliente')

                    # armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
                    # socket.SOCK_STREAM = socket orientado a conexión
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    # Como es un socket orientado a conexión debemos conectarlo a la dirección acordada
                    client_socket.connect((hostname, port))

                    print("Enviando mensaje a servidor")

                    client_socket.send(recv_message.encode())

                    # Finalmente esperamos una respuesta
                    # Para ello debemos definir el tamaño del buffer de recepción
                    buffer_size = 4096
                    message = client_socket.recv(buffer_size)

                    # Pasamos el mensaje de bytes a string
                    decoded_message = message.decode()

                    # cerramos la conexión
                    client_socket.close()
                    
                    new_socket.send(decoded_message.encode())
                     

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

```

**Decisiones de diseño:**

- [Decisión 1]
- [Decisión 2]

### 3.2 Bloqueo de sitios prohibidos

**Implementación:**

```python
import socket
from types import new_class
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

def esta_bloqueado(hostname: str, blocked_list: list) -> bool:
    hostname = hostname.lower()
    for blocked in blocked_list:
        if hostname in blocked.lower():
            return True
    return False

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

                    # obtenemos el host
                    hostname, port = obtener_target_host(response["headers"])

                    # verificamos si el host está bloqueado
                    if esta_bloqueado(hostname, config["blocked"]):
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

                    # Creamos socket cliente
                    print('Creando socket - Cliente')

                    # armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
                    # socket.SOCK_STREAM = socket orientado a conexión
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    # Como es un socket orientado a conexión debemos conectarlo a la dirección acordada
                    client_socket.connect((hostname, port))

                    print("Enviando mensaje a servidor")

                    client_socket.send(recv_message.encode())

                    # Finalmente esperamos una respuesta
                    # Para ello debemos definir el tamaño del buffer de recepción
                    buffer_size = 4096
                    message = client_socket.recv(buffer_size)

                    # Pasamos el mensaje de bytes a string
                    decoded_message = message.decode()

                    # cerramos la conexión
                    client_socket.close()
                    
                    new_socket.send(decoded_message.encode())
                     

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
```

**Decisiones de diseño:**

- [Cómo se verifica si un sitio está bloqueado]
- [Qué respuesta se envía cuando el sitio está bloqueado]

### 3.3 Modificación de headers

**Implementación:**

```python
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

def esta_bloqueado(hostname: str, blocked_list: list) -> bool:
    hostname = hostname.lower()
    for blocked in blocked_list:
        if hostname in blocked.lower():
            return True
    return False

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

                    # obtenemos el host
                    hostname, port = obtener_target_host(response["headers"])

                    # verificamos si el host está bloqueado
                    if esta_bloqueado(hostname, config["blocked"]):
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

                    # Finalmente esperamos una respuesta
                    # Para ello debemos definir el tamaño del buffer de recepción
                    buffer_size = 4096
                    message = client_socket.recv(buffer_size)

                    # Pasamos el mensaje de bytes a string
                    decoded_message = message.decode()

                    # cerramos la conexión
                    client_socket.close()
                    
                    new_socket.send(decoded_message.encode())
                     

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
```

**Decisiones de diseño:**

- [Qué headers se modifican]
- [Por qué se modifican]

### 3.4 Reemplazo de contenido

**Implementación:**

```python
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

def esta_bloqueado(hostname: str, blocked_list: list) -> bool:
    hostname = hostname.lower()
    for blocked in blocked_list:
        if hostname in blocked.lower():
            return True
    return False

def replace_content(body: str, forbidden_words: list[dict[str, str]]) -> str:
    for i in forbidden_words:
        for key, value in i.items():
            body = body.replace(key, value)

    return body


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

                    # obtenemos el host
                    hostname, port = obtener_target_host(response["headers"])

                    # verificamos si el host está bloqueado
                    if esta_bloqueado(hostname, config["blocked"]):
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

                    # Finalmente esperamos una respuesta
                    # Para ello debemos definir el tamaño del buffer de recepción
                    buffer_size = 4096
                    message = client_socket.recv(buffer_size)

                    # Pasamos el mensaje de bytes a string
                    decoded_message = message.decode()
                    # Parseamos el mensaje 
                    parsed_message = parse_HTTP_message(decoded_message)
                    parsed_message["body"] = replace_content(parsed_message["body"], config["forbidden_words"])
                    new_response = create_HTTP_message(parsed_message)

                    # cerramos la conexión
                    client_socket.close()
                    
                    new_socket.send(new_response.encode())
                     

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
```

**Decisiones de diseño:**

- [Cómo se identifican las palabras prohibidas]
- [Cómo se realiza el reemplazo]

### 3.5 Manejo de mensajes grandes

**Preguntas:**

1. **¿Cómo sé si llegó el mensaje completo?**
   
   [Respuesta]

2. **¿Qué pasa si los headers no caben en mi buffer?**
   
   [Respuesta]

3. **¿Cómo sé que el HEAD llegó completo?**
   
   [Respuesta]

4. **¿Y el BODY?**
   
   [Respuesta]

**Implementación:**

```python
# Código para manejar mensajes grandes
# Tu implementacimport socket
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
        print('Socket del servidor cerrado')ión aquí
```

**Decisiones de diseño:**

- [Decisión 1]
- [Decisión 2]

---

## 4. Pruebas realizadas

### 4.1 Pruebas con navegador

#### Test 1: Sitio prohibido

- **URL probada:** http://cc4303.bachmann.cl/secret
- **Resultado esperado:** Error 403
- **Resultado obtenido:** [Describe el resultado]
- **Observaciones:** [Observaciones]

#### Test 2: Modificación de headers

- **URL probada:** http://cc4303.bachmann.cl/
- **Resultado esperado:** Contenido modificado según cambios en headers
- **Resultado obtenido:** [Describe el resultado]
- **Observaciones:** [Observaciones]

#### Test 3: Reemplazo de palabras

- **URL probada:** http://cc4303.bachmann.cl/replace
- **Resultado esperado:** Palabras prohibidas reemplazadas
- **Resultado obtenido:** [Describe el resultado]
- **Observaciones:** [Observaciones]

#### Test 4: Sitios normales

- **URL probada:** http://cc4303.bachmann.cl/
- **Resultado esperado:** Sitio accesible normalmente
- **Resultado obtenido:** [Describe el resultado]
- **Observaciones:** [Observaciones]

### 4.2 Pruebas con buffer pequeño

#### Caso 1: Buffer más pequeño que el mensaje, más grande que headers

- **Tamaño del buffer:** [X]
- **Tamaño del mensaje:** [Y]
- **Tamaño de los headers:** [Z]
- **Resultado:** [Describe el resultado]
- **Observaciones:** [Observaciones]

#### Caso 2: Buffer más pequeño que headers, más grande que start line

- **Tamaño del buffer:** [X]
- **Tamaño de los headers:** [Y]
- **Tamaño de la start line:** [Z]
- **Resultado:** [Describe el resultado]
- **Observaciones:** [Observaciones]

### 4.3 Pruebas con curl

#### Sin proxy

```bash
curl example.com
```

**Resultado:** [Describe el resultado]

#### Con proxy

```bash
curl example.com -x IP_VM:8000
```

**Resultado:** [Describe el resultado]

---

## 5. Dificultades encontradas

[Dificultad 1]

[Dificultad 2]

[Dificultad 3]

---

## 6. Conclusiones

[Conclusión 1]

[Conclusión 2]

[Conclusión 3]

---

## 7. Referencias

- [Referencia 1]
- [Referencia 2]
- [Referencia 3]
