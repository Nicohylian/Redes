from SocketTCP import SocketTCP
import sys
import time

def main(argv):
    if(len(argv)==3):
        return (argv[1], int(argv[2]))

if __name__ == "__main__":
    

    buff_size = 16
    address = main(sys.argv)

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
    client_socketTCP.debug = False
    client_socketTCP.lost = True
    client_socketTCP.connect(address)
    

    text = ""
    while True:
        try:
            parrafo = input()
            text += parrafo
        except:
            break
    
    print("Con control de congestion")
    i = 5
    while i > 0:
        client_socketTCP.number_of_sent_segment = 0
        start = time.perf_counter()
        client_socketTCP.send(text.encode(), "go_back_n")
        end = time.perf_counter()
        print("Tiempo demorado en enviar el archivo: ", (end - start), " segundos\nNumero de segmentos enviados: ", client_socketTCP.number_of_sent_segment)
        i -=1
    
    print("Sin control de congestion")
    i = 5
    while i > 0:
        client_socketTCP.number_of_sent_segment = 0
        start = time.perf_counter()
        client_socketTCP.send(text.encode(), "go_back_n_without_control")
        end = time.perf_counter()
        print("Tiempo demorado en enviar el archivo: ", (end - start), " segundos\nNumero de segmentos enviados: ", client_socketTCP.number_of_sent_segment)
        i -=1


    client_socketTCP.close()

    
