from router import fragment_IP_packet, reassemble_IP_packet, create_packet, parse_packet
import socket
import random

if __name__ == "__main__":

    
    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    mtu = 50
    message_1 = "Este es un mensaje de prueba para verificar la fragmentación y reensamblaje de paquetes IP.".encode()
    message_2 = "Otro mensaje corto.".encode()

    ip = "127.0.0.1"
    port = 8881
    id_1 = random.randint(0, 65535)
    id_2 = random.randint(0, 65535)
    packet_1 = create_packet({
        "IP": ip.encode(),
        "port": str(port).encode(),
        "ID": id_1,
        "flags": b"0",
        "ttl": 5,
        "offset": 0,
        "size": len(message_1),
        "data": message_1
    })

    packet_2 = create_packet({
        "IP": ip.encode(),
        "port": str(port).encode(),
        "ID": id_2,
        "flags": b"0",
        "ttl": 5,
        "offset": 0,
        "size": len(message_2),
        "data": message_2})
    
    fragments_1 = fragment_IP_packet(packet_1, mtu)
    fragments_2 = fragment_IP_packet(packet_2, mtu)

    list_of_fragments = fragments_1 + fragments_2
    random.shuffle(list_of_fragments)
    for fragment in list_of_fragments:
        router_socket.sendto(fragment, (ip, port))
        print(f"Enviando fragmento: {fragment}")
    

