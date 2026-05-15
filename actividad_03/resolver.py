import socket

#IP maquina virtual
IP_VM = "0.0.0.0"
PORT = 8000

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IP_VM, PORT))

    print(f"Resolver escuchando en {IP_VM}:{PORT}")

    while True:
        data, client_address = sock.recvfrom(4096)

        print("\n--- Mensaje DNS recibido ---")
        print("Cliente:", client_address)
        print("Bytes recibidos:")
        print(data)

if __name__ == "__main__":
    main()