# esta fnción se encarga de tomar un mensaje HTTP 
# y lo transfiere a una estructura de datos que le 
# permita acceder fácilmente la información del mensaje.
def parse_HTTP_message(http_message):
    head, body = http_message.split("\r\n\r\n")
    lines = head.split("\r\n")
    start_line = lines[0]
    headers= {}
    for i in lines[1:]:
        key, value = i.split(":", 1)
        headers[key] = value.strip()
    return {
        "start_line": start_line,
        "headers": headers,
        "body": body
    }
# esta función toma la estructura de datos entregada por
#parse_HTTP y la convierte en un mensaje HTTP
def create_HTTP_message(data):
    message = ""
    message += data["start_line"] + "\r\n"

    for key, value in data["headers"].items():
        message += key + ": " + value  + "\r\n"
    message += "\r\n"

    message += data["body"]

    return message
