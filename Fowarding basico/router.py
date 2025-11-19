import socket
import sys

router_ip = ""
router_puerto = 0
router_rutas = ""
round = None

class RotateTableRoutes:
    def __init__(self, routes_file_name):
        self.routes = []
        self.areas = []
        current_index = 0
        init_index = 0
        last_index = 0
        current_line = "127.0.0.1 0 0 127.0.0.1 0"
        route_fields = current_line.strip().split(" ")
        first_line = True
        with open(routes_file_name, 'r') as routes_file:
            for line in routes_file:
                line_fields = line.strip().split(" ")
                if line_fields[0] != route_fields[0] or line_fields[1] != route_fields[1] or line_fields[2] != route_fields[2]:
                    if not first_line:
                        last_index = current_index - 1
                        self.areas.append((init_index, last_index))
                    else:
                        first_line = False

                    init_index = current_index
                    current_line = line
                    route_fields = current_line.strip().split(" ")
                current_index += 1
                self.routes.append(line)
            last_index = current_index - 1
            self.areas.append((init_index, last_index))
        self.current_index = 0
        self.total_routes = len(self.routes)
    
    def get_routes_list(self):
        return self.routes.copy()
    


    def find_route(self):
        for area in self.areas:
            init_index, last_index = area
            if init_index <= self.current_index <= last_index:
                first_third = self.routes[:init_index]
                third_third = self.routes[last_index+1:]
                first_half = self.routes[init_index:self.current_index+1]
                second_half = self.routes[self.current_index+1:last_index+1]
                self.routes = first_third + second_half + first_half + third_third
                break
        self.current_index = 0

    def continue_round_robin(self):
        self.current_index = (self.current_index + 1) % self.total_routes
    


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
    parse_IP_packet = {"IP": fields[0], "port": fields[1], "ttl": fields[2] ,"data": fields[3]}
    return parse_IP_packet

def create_packet(parsed_IP_packet):
    packet = parsed_IP_packet["IP"] + b";" + parsed_IP_packet["port"] + b";" + parsed_IP_packet["ttl"] + b";" + parsed_IP_packet["data"]
    return packet

def check_routes(routes_file_name, destination_address):
    global round
    if round is None:
        round = RotateTableRoutes(routes_file_name)
        
    route_list = round.get_routes_list()
    for line in route_list:
        route_fields = line.strip().split(" ")
        route_ip = route_fields[0]
        initial_port = int(route_fields[1])
        end_port = int(route_fields[2])
        next_hop_ip = route_fields[3]
        next_hop_port = int(route_fields[4])
        if route_ip == destination_address[0] and initial_port <= destination_address[1] and destination_address[1] <= end_port:
            round.find_route()
            return (next_hop_ip, next_hop_port)
        else:
            round.continue_round_robin()
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
    
    try:
        while True:
            packet_data, address = router_socket.recvfrom(4096)
            parsed_packet = parse_packet(packet_data)
            if parsed_packet["ttl"].decode() == "0":
                print(f"Se recibio el paquete {parsed_packet.get("IP").decode()} con TTL 0")
                continue
            
            destination_ip = parsed_packet["IP"].decode()
            destination_port = int(parsed_packet["port"].decode())
            if (destination_ip,destination_port) == (router_ip, router_puerto):
                print("Paquete recibido para este router:", parsed_packet["data"].decode())

            else:
                next_hop = check_routes(router_rutas, (destination_ip, destination_port))
                if next_hop is not None:
                    next_hop_ip, next_hop_port = next_hop
                    parsed_packet["ttl"] = str(int(parsed_packet["ttl"].decode()) - 1).encode()
                    router_socket.sendto(create_packet(parsed_packet), (next_hop_ip, next_hop_port))
                    print(f"redirigiendo paquete {destination_ip} con destino final {destination_ip}:{destination_port} \ndesde {router_ip}:{router_puerto} hacia {next_hop_ip}:{next_hop_port}")
                else:
                    print(f"No hay rutas hacia {destination_ip}:{destination_port} para el paquete {packet_data.decode()}")
    except KeyboardInterrupt:
        print("Router detenido por el usuario.")
        router_socket.close()
      
