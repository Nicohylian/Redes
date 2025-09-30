from SocketTCP import SocketTCP

if __name__ == "__main__":

    buff_size = 16
    address = ('localhost', 8000)

    client_socket: SocketTCP = SocketTCP()
    client_socket.addres_destiny = address
    

    while True:
        input_data = input()
        message = input_data
        for i in range(0, len(message), buff_size):
            chunk = "1|||0|||0|||"+str(i)+"|||"+message[i:i+buff_size]
            client_socket.socket.sendto(chunk.encode(), address)

        