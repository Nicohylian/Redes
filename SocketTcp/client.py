from SocketTcp.SocketTCP import SocketTCP
import sys

def main(argv):
    if(len(argv)==3):
        return (argv[1], int(argv[2]))

if __name__ == "__main__":

    buff_size = 16
    address = main(sys.argv)
    
    client_socketTCP = SocketTCP()
    client_socketTCP.debug = False
    client_socketTCP.connect(address)
    # test 1
    message = "Mensje de len=16".encode()
    client_socketTCP.send(message)
    # test 2
    message = "Mensaje de largo 19".encode()
    client_socketTCP.send(message)
    # test 3
    message = "Mensaje de largo 19".encode()
    client_socketTCP.send(message)

    text = ""
    while True:
        try:
            parrafo = input()
            text += parrafo
        except:
            break
    
    client_socketTCP.send(text.encode())

    client_socketTCP.close()
