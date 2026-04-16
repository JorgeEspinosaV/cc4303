import socket
from dnslib import DNSRecord, QTYPE
direccion = "192.33.4.12"
port = 53
Buffer = 4096

def parse_dns_message(data):
    d = DNSRecord.parse(data)
    qname = str(d.get_q().get_qname())
    ancount = d.header.a
    nscount = d.header.auth
    arcount = d.header.ar
    parsed_message = {
        "Qname": qname,
        "ANCOUNT": ancount,
        "NSCOUNT": nscount,
        "ARCOUNT": arcount,
        "Answer": [],
        "Authority": [],
        "Additional": [],
    }

    for rr in d.rr:
        parsed_message["Answer"].append({
            "name": str(rr.rname),
            "type": QTYPE[rr.rtype],
            "data": str(rr.rdata)
        })

    for rr in d.auth:
        parsed_message["Authority"].append({
            "name": str(rr.rname),
            "type": QTYPE[rr.rtype],
            "data": str(rr.rdata)
        })
    for rr in d.ar:
        parsed_message["Additional"].append({
            "name": str(rr.rname),
            "type": QTYPE[rr.rtype],
            "data": str(rr.rdata)
        })
    return parsed_message
    
def send_dns_query(q_bytes, server_ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = (server_ip, port)
    try:
        # lo enviamos, hacemos cast a bytes de lo que resulte de la función pack() sobre el mensaje
         sock.sendto(q_bytes, server_address)
         # En data quedará la respuesta a nuestra consulta
         data, _ = sock.recvfrom(Buffer)
         # le pedimos a dnslib que haga el trabajo de parsing por nosotros 
         return data
    finally:
         sock.close()

def resolver(mssg):
    respuesta = send_dns_query(mssg, direccion)
    return respuesta

#creamos socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('localhost', 8000))
while True:
    data, addr = sock.recvfrom(4096)
    print("Mensaje recibido desde:", addr)
    print(data)
    respuesta = resolver(data)
    sock.sendto(respuesta, addr)

