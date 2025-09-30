from SocketTCP import SocketTCP

if __name__ == "__main__":
    buff_size = 32
    address = ('localhost', 8000)

    server_socket = SocketTCP()

    server_socket.socket.bind(address)


    
    while True:
        data, addres_data = server_socket.socket.recvfrom(buff_size)
        message = server_socket.parse_segment(data.decode())
        print(message['DATA']) 