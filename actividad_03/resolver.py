import socket
from dnslib import DNSRecord
from dnslib.dns import CLASS, QTYPE

#IP maquina virtual
IP_VM = "0.0.0.0"
#Puerto de donde escuchar
PORT = 8000

#4
ROOT_SERVER = "192.33.4.12"
DNS_PORT = 53

#envia una consulta DNS en bytes a un servidor DNS
#y retorna la respuesta en bytes
def send_dns_query(query_data, server_ip):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    try:
        sock.sendto(query_data, (server_ip, DNS_PORT))
        response, _ = sock.recvfrom(4096)
        return response

    except socket.timeout:
        print(f"Timeout consultando a {server_ip}")
        return None

    finally:
        sock.close()

#revisa si la seccion Answer contiene una respuesta type A
def has_a_answer(dns_record):

    for rr in dns_record.rr:
        if QTYPE.get(rr.rtype) == "A":
            return True

    return False  

#busca la primera IP type A en Additional
def get_first_a_from_additional(dns_record):

    for rr in dns_record.ar:
        if QTYPE.get(rr.rtype) == "A":
            return str(rr.rdata)

    return None

#busca el primer Name Server en Authority
def get_first_ns_from_authority(dns_record):

    for rr in dns_record.auth:
        if QTYPE.get(rr.rtype) == "NS":
            return str(rr.rdata)

    return None

#Resuelve una consulta DNS y recibe el mensaje original de dig en bytes 
#y retorna una respuesta DNS en bytes.
def resolver(mensaje_consulta, server_ip=ROOT_SERVER, server_name="."):

    query_info = parse_dns_message(mensaje_consulta)
    domain = query_info["qname"]

    print(f"(debug) Consultando '{domain}' a '{server_name}' con dirección IP '{server_ip}'")

    response = send_dns_query(mensaje_consulta, server_ip)

    if response is None:
        return None

    dns_response = DNSRecord.parse(response)

    # Caso b: si la respuesta contiene un registro A en Answer, retornamos esa respuesta
    if has_a_answer(dns_response):
        print(f"(debug) Respuesta tipo A encontrada para '{domain}'")
        return response

    # Caso c.i: si viene una IP tipo A en Additional, preguntamos a esa IP
    next_ip = get_first_a_from_additional(dns_response)

    if next_ip is not None:
        print(f"(debug) Delegación encontrada. Siguiente IP: {next_ip}")
        return resolver(mensaje_consulta, next_ip, "NS desde Additional")

    # Caso c.ii: si no viene IP en Additional, tomamos un NS desde Authority
    next_ns = get_first_ns_from_authority(dns_response)

    if next_ns is not None:
        print(f"(debug) No hay IP en Additional. Resolviendo IP del NS: {next_ns}")

        ns_query = DNSRecord.question(next_ns, qtype="A")
        ns_response = resolver(ns_query.pack())

        if ns_response is None:
            return None

        parsed_ns_response = DNSRecord.parse(ns_response)

        for rr in parsed_ns_response.rr:
            if QTYPE.get(rr.rtype) == "A":
                ns_ip = str(rr.rdata)
                print(f"(debug) IP encontrada para NS {next_ns}: {ns_ip}")
                return resolver(mensaje_consulta, ns_ip, next_ns)

    # Caso d: otro tipo de respuesta
    print(f"(debug) No se pudo resolver '{domain}' con esta respuesta")
    return None

#recibe un mensaje DNS en bytes y lo transforma en
#una estructura de datos manejable usando dnslib
def parse_dns_message(data):
    #parsemaos los bytes DNS
    dns_record = DNSRecord.parse(data)
    #pregunta del mensaje DNS
    question = dns_record.get_q()

    #diccionario
    parsed_message = {
        "qname": str(question.get_qname()),
        "qtype": QTYPE.get(question.qtype),
        "qclass": CLASS.get(question.qclass),
        "ancount": dns_record.header.a,
        "nscount": dns_record.header.auth,
        "arcount": dns_record.header.ar,
        "answer": dns_record.rr,
        "authority": dns_record.auth,
        "additional": dns_record.ar,
    }

    return parsed_message

#pritnea el mensaje DNS parseado
def print_parsed_message(parsed_message):

    print("\n--- Mensaje DNS parseado ---")
    print("Qname:", parsed_message["qname"])
    print("Tipo de consulta:", parsed_message["qtype"])
    print("Clase de consulta:", parsed_message["qclass"])
    print("ANCOUNT:", parsed_message["ancount"])
    print("NSCOUNT:", parsed_message["nscount"])
    print("ARCOUNT:", parsed_message["arcount"])

    print("\nAnswer:")
    print(parsed_message["answer"])

    print("\nAuthority:")
    print(parsed_message["authority"])

    print("\nAdditional:")
    print(parsed_message["additional"])


def main():
    #socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #asociamos el socket a una direccion y puerto 
    sock.bind((IP_VM, PORT))

    print(f"Resolver escuchando en {IP_VM}:{PORT}")

    while True:
        #espera recibir un mensaje
        data, client_address = sock.recvfrom(4096)

        print("\n--- Mensaje DNS recibido ---")
        print("Cliente:", client_address)
        print("Bytes recibidos:")
        print(data)

        parsed_message = parse_dns_message(data)
        print_parsed_message(parsed_message)

        response = resolver(data)
        if response is not None:
            sock.sendto(response, client_address)

if __name__ == "__main__":
    main()