import socket
from dnslib import DNSRecord, QTYPE
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
    

#creamos socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('localhost', 8000))
while True:
    data, addr = sock.recvfrom(4096)
    print("Mensaje recibido desde:", addr)
    print(data)
    parsed = parse_dns_message(data)
    print(parsed)

