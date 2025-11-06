from SocketTCP import SocketTCP

if __name__ == "__main__":
    buff_size = 16
    address = ('localhost', 8000)

     
        
    server_socketTCP = SocketTCP()
    server_socketTCP.debug = False
    server_socketTCP.bind(address)
    connection_socketTCP, new_address = server_socketTCP.accept()

    # test 1
    buff_size = 16
    full_message = connection_socketTCP.recv(buff_size)
    print("Test 1 received:", full_message.decode())
    if full_message == "Mensje de len=16".encode(): print("Test 1: Passed")
    else: print("Test 1: Failed")

    # test 2
    buff_size = 19
    full_message = connection_socketTCP.recv(buff_size)
    print("Test 2 received:", full_message.decode())
    if full_message == "Mensaje de largo 19".encode(): print("Test 2: Passed")
    else: print("Test 2: Failed")

    # test 3
    buff_size = 14
    message_part_1 = connection_socketTCP.recv(buff_size)
    message_part_2 = connection_socketTCP.recv(buff_size)
    print("Test 3 received:", message_part_1.decode() + message_part_2.decode())
    if (message_part_1 + message_part_2) == "Mensaje de largo 19".encode(): print("Test 3: Passed")
    else: print("Test 3: Failed")

    first = True
    message = b""
    
    while first or connection_socketTCP.msg_left != 0:
        parrafo = connection_socketTCP.recv(buff_size)
        message += parrafo
        first = False
    
    print(message.decode())
    
    connection_socketTCP.recv_close()
