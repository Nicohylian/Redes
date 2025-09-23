import socket

if __name__ == "__main__":

    buff_size = 16
    address = ('localhost', 8000)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        input_data = input()
        message = input_data.encode()
        for i in range(0, len(message), buff_size):
            chunk = message[i:i+buff_size]
            client_socket.sendto(chunk, address)
        