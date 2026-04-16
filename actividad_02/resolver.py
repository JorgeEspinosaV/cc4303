import socket
from dnslib import DNSRecord, QTYPE
direccion = "192.33.4.12"
port = 53
buffer = 4096
#
def parse_dns_message(data):
    #Parsea los bytes
    d = DNSRecord.parse(data)
    #QNAME
    qname = str(d.get_q().get_qname())
    #ANCOUNT (Answer)
    ancount = d.header.a
    #NSCOUNT (Authority)
    nscount = d.header.auth
    #ARCOUNT (Additional)
    arcount = d.header.ar
    #Guardar información
    parsed_message = {
        "Qname": qname,
        "ANCOUNT": ancount,
        "NSCOUNT": nscount,
        "ARCOUNT": arcount,
        "Answer": [],
        "Authority": [],
        "Additional": [],
    }
    #Recorrer registros de Answer
    for rr in d.rr:
        parsed_message["Answer"].append({
            "name": str(rr.rname),
            "type": QTYPE[rr.rtype],
            "data": str(rr.rdata)
        })
    #Recorrer registros de Authority
    for rr in d.auth:
        parsed_message["Authority"].append({
            "name": str(rr.rname),
            "type": QTYPE[rr.rtype],
            "data": str(rr.rdata)
        })
    #Recorrer registros de Additional
    for rr in d.ar:
        parsed_message["Additional"].append({
            "name": str(rr.rname),
            "type": QTYPE[rr.rtype],
            "data": str(rr.rdata)
        })
    return parsed_message
# 
def send_dns_query(q_bytes, server_ip):
    #creamos socket sin conexion
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    server_address = (server_ip, port)
    try:
        # lo enviamos, consulta DNS a servidor
         sock.sendto(q_bytes, server_address)
         # En data quedará la respuesta a nuestra consulta
         data, _ = sock.recvfrom(buffer)
         # le pedimos a dnslib que haga el trabajo de parsing por nosotros 
         return data
    finally:
         #Cerramos socket
         sock.close()
#Función qeu resuelve las consultas DNS
def resolver(mssg, server_ip=direccion):
    #Enviar la query a servidor indicado
    answer = send_dns_query(mssg, server_ip)
    #PArsear respuesta recibida
    parsed = parse_dns_message(answer)
    #3.b: Si mensaje answer recibido tiene la respuesta a la cosulta
    for rr in parsed["Answer"]:
        if rr["type"] == "A":
            return answer
        
    ns_list = []
    #Si un registro es tipo NS
    for rr in parsed["Authority"]:
        if rr["type"] == "NS":
            ns_list.append(rr)

    if ns_list:
        #3c.i: Usar la direción IP contenida en Additional
        for rr in parsed["Additional"]:
            if rr["type"] == "A":
                return resolver(mssg, rr["data"])
            
        #3c.ii: Si no se encuentra laguna IP en la sección Additional, tomar el nombre de un NS
        ns_name = ns_list[0]["data"]
        #Contruir una nueva consulta
        ns_query = DNSRecord.question(ns_name, "A")
        #Convertir a bytes
        ns_query_bytes = ns_query.pack()
        #Recursividad para resolver la IP asociada al nombre de dominio del NS
        ns_response = resolver(ns_query_bytes)
        #Si no se puede resolverla IP del NS
        if ns_response is None:
            return None
        #Parsea respuesta que obtuvo la IP del NS
        parsed_ns = parse_dns_message(ns_response)
        for rr in parsed_ns["Answer"]:
            if rr["type"] == "A":
                ns_ip = rr["data"]
                return resolver(mssg, ns_ip)
    #3.d: Algún otro tipo de respuesta, ignorar
    return None

#creamos socket "servidor"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#Asociamos a puerto 8000
sock.bind(('localhost', 8000))
while True:
    #Espera consulta DNS
    data, addr = sock.recvfrom(4096)
    print("Mensaje recibido desde:", addr)
    print(data)
    #MAndar la query recibida a función resolver
    answer = resolver(data)
    #Si devolvió respuesta válida, enviar a cliente 
    if answer:
        sock.sendto(answer, addr)

