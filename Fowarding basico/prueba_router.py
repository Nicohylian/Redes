import sys
import socket

header_router = None
initial_IP = None
initial_port = None

def main(args):
    if len(args) != 4:
        print("Usage: python prueba_router.py <headers> <IP_router_inicial> <puerto_router_inincial>")
        return -1
    global header_router, initial_port, initial_IP
    header_router = args[1]
    initial_IP = args[2]
    initial_port = int(args[3])
    return 0

if __name__ == "__main__":
    i = main(sys.argv)
    if i != 0:
        sys.exit(i)
    
    prueba_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    header_router = header_router.replace(",", ";").encode()
    with open("archivo.txt", "r") as file:
        for line in file:
            data = line.strip().encode()
            packet = header_router + b";" + data
            prueba_socket.sendto(packet, (initial_IP, initial_port))
            print(f"Enviando paquete al router {initial_IP}:{initial_port} con datos: {data.decode()}")
    
    prueba_socket.close()