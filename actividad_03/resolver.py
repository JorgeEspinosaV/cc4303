import socket
from dnslib import DNSRecord
from dnslib.dns import CLASS, QTYPE

#IP maquina virtual
IP_VM = "0.0.0.0"
#Puerto de donde escuchar
PORT = 8000
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

if __name__ == "__main__":
    main()