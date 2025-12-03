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

def convert_digits(digits, mode, length=8):
    if mode == "encode":
        digits_str = str(digits)
        while len(digits_str) < length:
            digits_str = "0" + digits_str
        return digits_str.encode()
    elif mode == "decode":
        digits_str = digits.decode()
        return int(digits_str)


def parse_packet(IP_packet):
    fields = IP_packet.split(b";")
    parse_IP_packet = {"IP": fields[0], "port": fields[1], "ttl": fields[2],
                        "ID": fields[3], "offset": fields[4], "size": fields[5],
                        "flags": fields[6] ,"data": fields[7]}
    parse_IP_packet["ttl"] = convert_digits(parse_IP_packet["ttl"], "decode")
    parse_IP_packet["ID"] = convert_digits(parse_IP_packet["ID"], "decode")
    parse_IP_packet["offset"] = convert_digits(parse_IP_packet["offset"], "decode")
    parse_IP_packet["size"] = convert_digits(parse_IP_packet["size"], "decode")
    parse_IP_packet["flags"] = parse_IP_packet["flags"]
    return parse_IP_packet

def create_packet(parsed_IP_packet):
    packet = parsed_IP_packet["IP"] + b";" + parsed_IP_packet["port"] + b";" + \
            convert_digits(parsed_IP_packet["ttl"], "encode", 3) + b";" + convert_digits(parsed_IP_packet["ID"], "encode", 8) + b";" + \
            convert_digits(parsed_IP_packet["offset"], "encode", 8) + b";" + convert_digits(parsed_IP_packet["size"], "encode", 8) + b";" + \
            parsed_IP_packet["flags"] + b";" + parsed_IP_packet["data"]
    return packet

def fragment_IP_packet(IP_packet, mtu):
    if len(IP_packet) <= mtu:
        return [IP_packet]
    elif len(IP_packet) > mtu:
        fragments = []
        parsed_packet = parse_packet(IP_packet)
        header_size =  len(IP_packet) - parsed_packet["size"]
        max_data_size = mtu - header_size
        data = parsed_packet["data"]
        offset = parsed_packet["offset"]
        id = parsed_packet["ID"]
        while len(data) > 0:
            fragment_data = data[:max_data_size]
            data = data[max_data_size:]
            parsed_fragment = parse_packet(IP_packet)
            parsed_fragment["offset"] = offset
            parsed_fragment["size"] = len(fragment_data)
            if len(data) > 0:
                parsed_fragment["flags"] = b"1"
            else:
                parsed_fragment["flags"] = parsed_packet["flags"]
            parsed_fragment["data"] = fragment_data
            fragment_packet = create_packet(parsed_fragment)
            fragments.append(fragment_packet)
            offset += parsed_fragment["size"]
        
        return fragments
    
def reassemble_IP_packet(fragment_list):
    if len(fragment_list) == 0:
        return None
    elif len(fragment_list) == 1:
        parsed_fragment = parse_packet(fragment_list[0])
        if parsed_fragment["flags"] == b"0" and parsed_fragment["offset"] == 0:
            return fragment_list[0]
        else:
            return None
    else:
        fragments = []
        for fragment in fragment_list:
            parsed_fragment = parse_packet(fragment)
            fragments.append((parsed_fragment["offset"], parsed_fragment))
        fragments.sort(key=lambda x: x[0])
        reassembled_data = b""
        expected_offset = 0
        for offset, parsed_fragment in fragments:
            if offset != expected_offset:
                return None
            reassembled_data += parsed_fragment["data"]
            expected_offset += parsed_fragment["size"]
            last_flags = parsed_fragment["flags"]
        
        if last_flags != b"0":
            return None
        
        first_parsed_fragment = fragments[0][1]
        reassembled_packet = create_packet({
            "IP": first_parsed_fragment["IP"],
            "port": first_parsed_fragment["port"],
            "ttl": first_parsed_fragment["ttl"],
            "ID": first_parsed_fragment["ID"],
            "offset": 0,
            "size": len(reassembled_data),
            "flags": b"0",
            "data": reassembled_data
        })
        return reassembled_packet


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
        mtu = int(route_fields[5])
        if route_ip == destination_address[0] and initial_port <= destination_address[1] and destination_address[1] <= end_port:
            round.find_route()
            return (next_hop_ip, next_hop_port), mtu
        else:
            round.continue_round_robin()
    return None, None

if __name__ == "__main__":

    
    i = main(sys.argv)
    
    
    print("Iniciando router en la direccion: ", router_ip, ":", router_puerto)
    print("Cargando rutas desde el archivo: ", router_rutas)
    
    cache = {}
    
    
    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind((router_ip, router_puerto))

    if not router_socket.getblocking():
        router_socket.setblocking(True)
    
    router_socket.settimeout(None)
    
    
    while True:
        packet_data, address = router_socket.recvfrom(4096)
        parsed_packet = parse_packet(packet_data)
        if parsed_packet["ttl"] == 0:
            print(f"Se recibio el paquete {parsed_packet.get("IP").decode()} con TTL 0")
            continue
        
        destination_ip = parsed_packet["IP"].decode()
        destination_port = int(parsed_packet["port"].decode())
        if (destination_ip,destination_port) == (router_ip, router_puerto):
            id = parsed_packet["ID"]
            cache[id] = cache.get(parsed_packet["ID"], []) + [packet_data]
            fragment_list = cache[id]
            reassembled_packet = reassemble_IP_packet(fragment_list)
            if reassembled_packet is not None:
                parsed_packet = parse_packet(reassembled_packet)
                del cache[id]
                print("Paquete recibido para este router:", parsed_packet["data"].decode())
        else:
            next_hop, mtu = check_routes(router_rutas, (destination_ip, destination_port))
            if next_hop is not None:
                next_hop_ip, next_hop_port = next_hop
                parsed_packet["ttl"] = parsed_packet["ttl"] - 1
                fragments = fragment_IP_packet(create_packet(parsed_packet), mtu)

                for fragment in fragments:
                    router_socket.sendto(fragment, (next_hop_ip, next_hop_port))
                print(f"redirigiendo paquete {destination_ip} con destino final {destination_ip}:{destination_port} \ndesde {router_ip}:{router_puerto} hacia {next_hop_ip}:{next_hop_port}")
            else:
                print(f"No hay rutas hacia {destination_ip}:{destination_port} para el paquete {packet_data.decode()}")
    
      
