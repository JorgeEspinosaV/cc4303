import socket
from dnslib import DNSRecord

#creamos socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('localhost', 8000))
while True:
    data, addr = sock.recvfrom(4096)
    print("Mensaje recibido desde:", addr)
    print(data)

def parse_dns_message(data):
    d = DNSRecord.parse(data)

    ancount = d.header.a
    nscount = d.header.auth
    arcount = d.header.ar

    qname = str(d.get_q().get_qqname())