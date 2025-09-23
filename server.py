import socket

if __name__ == "__main__":
    buff_size = 16
    address = ('localhost', 8000)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_socket.bind(address)


    
    while True:
        data, addres_data = server_socket.recvfrom(buff_size)
        print(data.decode()) 