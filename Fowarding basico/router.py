import socket
import sys

router_ip = ""
router_puerto = 0
router_rutas = ""
round = None

class rountingTableRoutes:
    def __init__(self, routes_file_name):
        self.routes = []
        self.current_index = 0
        with open(routes_file_name, 'r') as routes_file:
            for line in routes_file:
                self.routes.append(line)
        self.total_routes = len(self.routes)
    
    def get_routes_list(self):
        return self.routes
    
    def update_index(self):
        self.current_index = (self.current_index + 1) % self.total_routes
    
    def round_robin(self):
        first_half = self.routes[:self.current_index]
        second_half = self.routes[self.current_index:]
        new_routes = second_half + first_half
        self.routes = new_routes
        self.current_index = 0


def main(argv):
    if len(argv) < 4:
        print("Favor de ingresar <router_IP> <router_puerto> <router_rutas>")
        return -1
    global router_ip, router_puerto, router_rutas
    router_ip = argv[1]
    router_puerto = int(argv[2])
    router_rutas = argv[3]
    return 0

def parse_packet(IP_packet):
    fields = IP_packet.split(b";")
    parse_IP_packet = {"IP": fields[0], "port": fields[1], "data": fields[2]}
    return parse_IP_packet

def create_packet(parsed_IP_packet):
    packet = parsed_IP_packet["IP"] + b";" + parsed_IP_packet["port"] + b";" + parsed_IP_packet["data"]
    return packet

def check_routes(routes_file_name, destination_address):
    global round
    if round is None:
        round = rountingTableRoutes(routes_file_name)
    route_list = round.get_routes_list()
    for line in route_list:
        round.update_index()
        route_fields = line.strip().split(" ")
        route_ip = route_fields[0]
        initial_port = int(route_fields[1])
        end_port = int(route_fields[2])
        next_hop_ip = route_fields[3]
        next_hop_port = int(route_fields[4])
        if route_ip == destination_address[0] and initial_port <= destination_address[1] and destination_address[1] <= end_port:
            round.round_robin()
            return (next_hop_ip, next_hop_port)
    return None

if __name__ == "__main__":
    i = main(sys.argv)
    
    
    print("Iniciando router en la direccion: ", router_ip, ":", router_puerto)
    print("Cargando rutas desde el archivo: ", router_rutas)
    
    
    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind((router_ip, router_puerto))

    if not router_socket.getblocking():
        router_socket.setblocking(True)
    
    router_socket.settimeout(None)
    

    while True:
        packet_data, address = router_socket.recvfrom(4096)
        parsed_packet = parse_packet(packet_data)
        destination_ip = parsed_packet["IP"].decode()
        destination_port = int(parsed_packet["port"].decode())
        if (destination_ip,destination_port) == (router_ip, router_puerto):
            print("Paquete recibido para este router:", parsed_packet["data"].decode())
            
        else:
            next_hop = check_routes(router_rutas, (destination_ip, destination_port))
            if next_hop is not None:
                next_hop_ip, next_hop_port = next_hop
                router_socket.sendto(create_packet(parsed_packet), (next_hop_ip, next_hop_port))
                print(f"redirigiendo paquete {packet_data.decode()} con destino final {destination_ip}:{destination_port} desde {router_ip}:{router_puerto} hacia {next_hop_ip}:{next_hop_port}")
            else:
                print(f"No hay rutas hacia {destination_ip}:{destination_port} para el paquete {packet_data.decode()}")
    
        
    
