from SocketTCP import SocketTCP

segment = SocketTCP.create_segment(
    syn=1,
    ack=0,
    fin=0,
    seq=25,
    data=b"Mensaje de prueba"
)

parsed = SocketTCP.parse_segment(segment)

print("Segmento original:")
print(segment)

print("Segmento parseado:")
print(parsed)

print("SYN:", parsed["SYN"])
print("ACK:", parsed["ACK"])
print("FIN:", parsed["FIN"])
print("SEQ:", parsed["SEQ"])
print("DATA:", parsed["DATA"])