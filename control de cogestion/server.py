from SocketTCP import SocketTCP
import sys
import time

def main(argv):
    if(len(argv)==3):
        return (argv[1], int(argv[2]))

if __name__ == "__main__":
    buff_size = 32
    address = main(sys.argv)

    """server_socket = SocketTCP()

    server_socket.bind(address)
    connection_socket, new_address = server_socket.accept()


    
    while True:
        data, addres_data = connection_socket.socket.recvfrom(buff_size)
        message = server_socket.parse_segment(data.decode())
        print(message['DATA']) """
     
        
    server_socketTCP = SocketTCP()
    
    server_socketTCP.bind(address)
    connection_socketTCP, new_address = server_socketTCP.accept()
    connection_socketTCP.lost= False

    print("Con control de congestion")
    i = 5
    while i > 0:
        connection_socketTCP.number_of_sent_segment = 0
        first = True
        message = b""
        start = time.perf_counter()
        while first or connection_socketTCP.msg_left != 0:
            parrafo = connection_socketTCP.recv(buff_size, "go_back_n")
            message += parrafo
            first = False
        end = time.perf_counter()
        print("Tiempo demorado en enviar el archivo: ", (end - start), " segundos\nNumero de segmentos enviados: ", connection_socketTCP.number_of_sent_segment)
        i -= 1
    
    print("Sin control de congestion")
    i = 5
    while i > 0:
        connection_socketTCP.number_of_sent_segment = 0
        first = True
        message = b""
        start = time.perf_counter()
        while first or connection_socketTCP.msg_left != 0:
            parrafo = connection_socketTCP.recv(buff_size, "go_back_n")
            message += parrafo
            first = False
        end = time.perf_counter()
        print("Tiempo demorado en enviar el archivo: ", (end - start), " segundos\nNumero de segmentos enviados: ", connection_socketTCP.number_of_sent_segment)
        i -= 1
    
    connection_socketTCP.recv_close()
    server_socketTCP.close()

    
