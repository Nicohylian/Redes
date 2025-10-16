from SocketTCP import SocketTCP

if __name__ == "__main__":

    buff_size = 16
    address = ('localhost', 8000)

    """client_socket: SocketTCP = SocketTCP()
    client_socket.connect(address)
    

    while True:
        input_data = input()
        message = input_data
        for i in range(0, len(message), buff_size):
            chunk = "1|||0|||0|||"+str(i)+"|||"+message[i:i+buff_size]
            client_socket.socket.sendto(chunk.encode(), client_socket.address_destiny)
            """
    client_socketTCP = SocketTCP()
    client_socketTCP.debug = True
    client_socketTCP.connect(address)
    # test 1
    message = "Mensje de len=10".encode()
    client_socketTCP.send(message, "go_back_n")
    # test 2
    message = "Mensaje de largo 19".encode()
    client_socketTCP.send(message, "go_back_n")
    # test 3
    message = "Mensaje de largo 19".encode()
    client_socketTCP.send(message, "go_back_n")

    client_socketTCP.close()
