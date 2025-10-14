import socket
import random

class SocketTCP:
    def __init__(self):
        self.socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address_origin=None
        self.address_destiny=None
        self.timeout=1
        self.seq=0
        self.new_msg = True
        self.msg_buff = []
        self.msg_left=0
        
    # recibe un string de estructura: SYN|||ACK|||FIN|||SEQ|||DATA
    @staticmethod
    def parse_segment(segment:str):
        segment_parts= segment.split('|||')
        header= {"SYN":False, "ACK":False, "FIN":False, "SEQ":None, "DATA":None}
        if segment_parts[0]=='1':
            header["SYN"]=True
        if segment_parts[1]=='1':
            header["ACK"]=True
        if segment_parts[2]=='1':
            header["FIN"]=True
        header["SEQ"]= int(segment_parts[3])
        if segment_parts[4]!='':
            header["DATA"]= segment_parts[4]

        return header
    
    @staticmethod
    def create_segment(header:dict):
        segment=''
        if header['SYN']:
            segment+='1|||'
        else:
            segment+='0|||'
        if header['ACK']:
            segment+='1|||'
        else:
            segment+='0|||'
        if header['FIN']:
            segment+='1|||'
        else:
            segment+='0|||'
        segment+= str(header['SEQ'])+'|||'
        if header['DATA'] is not None:
            segment+= header['DATA']

        return segment
        
        
    def bind(self, address):
        self.socket.bind(address)
        self.address_origin = address
        
    
    def connect(self, address):
        time_to_wait = 2
        self.socket.settimeout(self.timeout)
        self.seq = random.randint(0,101)
        syn_segment = self.create_segment({"SYN":True, "ACK":False, "FIN":False, "SEQ":self.seq, "DATA":None})   
        self.socket.sendto(syn_segment.encode(), address)
        while True:
            while True:
                try:
                    message, new_address = self.socket.recvfrom(32)
                    break
                except:
                    self.socket.sendto(syn_segment.encode(), address)
            header = self.parse_segment(message.decode())
            if (header["SYN"] and header["ACK"] and header["SEQ"]==self.seq+1):
                self.seq +=1
                self.address_destiny = new_address
                ack_segment = self.create_segment({"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq+1, "DATA":None})
                self.socket.sendto(ack_segment.encode(), self.address_destiny)
                break
            else:
                self.socket.sendto(syn_segment.encode(), address)
        while time_to_wait > 0:
            print("aqui")
            try:
                msg, _ = self.socket.recvfrom(32)
                self.socket.sendto(ack_segment.encode(), self.address_destiny)
            except:
                time_to_wait -= 1
            
        print("Conexion establecida con exito")
        return

            
    def accept(self):
        self.socket.settimeout(self.timeout)
        while True:
            while True:
                try:
                    message, client_address = self.socket.recvfrom(32)
                    header = self.parse_segment(message.decode())
                    break
                except:
                    pass
            if header["SYN"]:
                break

        self.address_destiny = client_address
        self.seq = header["SEQ"]+1
        
        new_socket = SocketTCP()
        new_address = (self.address_origin[0], self.address_origin[1]+self.seq)
        new_socket.bind(new_address)
        new_socket.address_destiny = self.address_destiny
        new_socket.seq = self.seq
        
        syn_ack_seg = self.create_segment({"SYN":True, "ACK":True, "FIN":False, "SEQ":self.seq,"DATA":None})
        new_socket.socket.sendto(syn_ack_seg.encode(), client_address)
        while True:
            while True:
                try:
                    ack_msg, _ = new_socket.socket.recvfrom(32)
                    break
                except:
                    new_socket.socket.sendto(syn_ack_seg.encode(), client_address)
            ack_header = self.parse_segment(ack_msg.decode())
            if ack_header["ACK"] and ack_header["SEQ"]==self.seq + 1:
                new_socket.seq +=1
                print("conexion establecida con exito")
                return new_socket, new_address
                
            else:
                new_socket.socket.sendto(syn_ack_seg.encode(), client_address)
    
    
    def send(self, message):
        msg = []
        cont = 0
        buff_size = 16
        message = message.decode() 
        self.socket.settimeout(self.timeout)
        length = str(len(message))
        segment = {"SYN":False, "ACK":False, "FIN":False, "SEQ":self.seq,"DATA":None}
        segment["DATA"] = length
        
        for i in range(0, len(message), buff_size):
            msg.append(message[i:i+buff_size])
         
        self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)      
        while True:           
            try:
                ack_msg, _ = self.socket.recvfrom(64)
                response = self.parse_segment(ack_msg.decode())
                if response["ACK"] and response["SEQ"] == (self.seq + len(length)):
                    print("largo recivido")
                    self.seq += len(length)         
                    break
                
            except:
                self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)    
                print("largo enviado nuevamente")
                
        while cont < len(msg):
            segment = {"SYN":False, "ACK":False, "FIN":False, "SEQ":self.seq,"DATA":None}
            segment["DATA"] = msg[cont]
            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
            print("dato enviado ", msg[cont])
            try:
                ack_msg, _ = self.socket.recvfrom(64)
                response = self.parse_segment(ack_msg.decode())
                if response["ACK"] and response["SEQ"]== (self.seq + len(msg[cont])):
                    print("confirmacion recibida")
                    self.seq += len(msg[cont])
                    cont+=1
            except:
                pass
        print("mensaje enviado")
              
    def recv(self, buff_size):
        full_msg = ""
        self.socket.settimeout(self.timeout)
        segment = {"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq,"DATA":None}
        
        #Dependiendo de en que caso estemos, vemos como procesamos el primer mensaje
        if self.msg_left == 0 and len(self.msg_buff) == 0:
            self.msg_buff = []
            while True:
                try:
                    msg, _ = self.socket.recvfrom(64)
                    message = self.parse_segment(msg.decode())
                    data = message["DATA"]
                    self.msg_left = int(data)
                    break
                except:
                    pass
            
            self.seq = message["SEQ"] + len(data)
            segment["SEQ"] = self.seq
            target = min(buff_size, self.msg_left)
            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
            while True:
                try:
                    msg, _ = self.socket.recvfrom(64)
                    message = self.parse_segment(msg.decode())
                    data = message["DATA"]
                    if (message["SEQ"] + len(data)!= self.seq):
                        break
                    else:
                        self.msg_left = int(data)
                        self.seq = message["SEQ"] + len(data)
                        segment["SEQ"] = self.seq
                        target = min(buff_size, self.msg_left)
                        self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
                except:
                    pass
          #Recibimos el mensaje completo aunque sea maytor que buff_size, si es mayor, el resto se guarda en una variable interna        
            while True:
                if (message["SEQ"] + len(data)!= self.seq):
                    self.msg_buff.append(data)
                    self.msg_left -= len(data)
                    self.seq = len(data) + message["SEQ"]
                    segment["SEQ"] = self.seq
                    self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
                        
                else:
                    old_data = self.msg_buff.pop()
                    self.msg_buff.append(data)
                    self.msg_left += len(old_data)
                    self.msg_left -= len(data)
                    self.seq = len(data) + message["SEQ"]
                    segment["SEQ"] = self.seq
                    self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
                    
                if self.msg_left > 0:
                    while True:
                        try:
                            msg, _ = self.socket.recvfrom(1024)
                            message = self.parse_segment(msg.decode())
                            data = message["DATA"]
                            break
                        except:
                            pass
                    
                else:
                    break
        #Caso en el que terminamos de recibir un mensaje        
        elif self.msg_left == 0 and len(self.msg_buff) != 0:
            data = ""
            target = min(len("".join(self.msg_buff)), buff_size)
                
                    
        while len(full_msg) < target:
            current_data = self.msg_buff[0]
            if len(full_msg) + len(current_data) > target:
                data_to_copy = current_data[0:(target-len(full_msg))]
                self.msg_buff[0] = current_data[(target-len(full_msg)):]
                full_msg += data_to_copy
            else:
                self.msg_buff.pop(0)
                full_msg += current_data
       
        return full_msg.encode()

    def close(self):
        self.socket.sendto(self.create_segment({"SYN":False, "ACK":False, "FIN":True, "SEQ":self.seq, "DATA":None}).encode(), self.address_destiny)
        while True:
            try:
                end_message,_ = self.socket.recvfrom(32)
                break
            except:
                pass
        end_header = self.parse_segment(end_message.decode())
        if end_header["FIN"] and end_header["ACK"] and (end_header["SEQ"] == self.seq+1):
            self.seq += 1
            self.socket.sendto(self.create_segment({"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq+1, "DATA":None}).encode(), self.address_destiny)
            self.socket.close()
            print("conexion terminada con exito")

    def recv_close(self):
        while True:
            try:
                end_message, addr = self.socket.recvfrom(32)
                break
            except:
                pass
        end_header = self.parse_segment(end_message.decode())
        if end_header["FIN"] and end_header["SEQ"] == self.seq:
            self.seq += 1
            self.socket.sendto(self.create_segment({"SYN":False, "ACK":True, "FIN":True, "SEQ":self.seq, "DATA":None}).encode(), addr)
            while True:
                try:
                    end_message, addr = self.socket.recvfrom(32)
                    break
                except:
                    pass
            end_header = self.parse_segment(end_message.decode())
            if end_header["ACK"] and end_header["SEQ"] == self.seq+1:
                self.socket.close()
                print("conexion terminada con exito")
