import socket
import random

class SocketTCP:
    def __init__(self):
        self.socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address_origin=None
        self.address_destiny=None
        self.timeout=1.0
        self.seq:int =0
        self.new_msg = True
        self.msg_buff = []
        self.msg_left=0
        self.debug = False
        
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
        seq_str = segment_parts[3].replace('|', '').strip()
        header["SEQ"]= int(seq_str)
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
        segment+= str(header['SEQ']).zfill(8)+'|||'
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
        if self.debug: print("Enviando mensaje: ", syn_segment)
        while True:
            while True:
                try:
                    message, new_address = self.socket.recvfrom(32)
                    break
                except:
                    self.socket.sendto(syn_segment.encode(), address)
                    if self.debug: print("Reenviando mensaje: ", syn_segment)
            header = self.parse_segment(message.decode())
            if (header["SYN"] and header["ACK"] and header["SEQ"]==self.seq+1):
                self.seq +=2
                self.address_destiny = new_address
                ack_segment = self.create_segment({"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq, "DATA":None})
                self.socket.sendto(ack_segment.encode(), self.address_destiny)
                if self.debug: print("Enviando mensaje: ", ack_segment)
                break
            else:
                self.socket.sendto(syn_segment.encode(), address)
                if self.debug: print("Reenviando mensaje: ", syn_segment)
        while time_to_wait > 0:
            print("aqui")
            try:
                msg, _ = self.socket.recvfrom(32)
                self.socket.sendto(ack_segment.encode(), self.address_destiny)
                if self.debug: print("Reenviando mensaje: ", ack_segment)
            except:
                time_to_wait -= 1
            
        print("Conexion establecida con exito")
        return

            
    def accept(self):
        self.socket.settimeout(self.timeout)
        while True:
            while True:
                try:
                    message, client_address = self.socket.recvfrom(23)
                    header = self.parse_segment(message.decode())
                    break
                except:
                    pass
            if header["SYN"]:
                break

        self.address_destiny = client_address
        self.seq = header["SEQ"]+1
        
        new_socket = SocketTCP()
        new_socket.debug = self.debug
        new_address = (self.address_origin[0], self.address_origin[1]+self.seq)
        print("nueva direccion del servidor: ", new_address)
        new_socket.bind(new_address)
        new_socket.address_destiny = self.address_destiny
        new_socket.seq = self.seq
        new_socket.socket.settimeout(self.timeout)
        syn_ack_seg = self.create_segment({"SYN":True, "ACK":True, "FIN":False, "SEQ":self.seq,"DATA":None})
        new_socket.socket.sendto(syn_ack_seg.encode(), client_address)
        if self.debug: print("Enviando mensaje: ", syn_ack_seg)
        while True:
            while True:
                try:
                    ack_msg, _ = new_socket.socket.recvfrom(23)
                    break
                except socket.timeout:
                    new_socket.socket.settimeout(self.timeout)
                    new_socket.socket.sendto(syn_ack_seg.encode(), client_address)
                    if self.debug: print("Reenviando mensaje: ", syn_ack_seg)
            ack_header = self.parse_segment(ack_msg.decode())
            if ack_header["ACK"] and ack_header["SEQ"]==self.seq + 1:
                new_socket.seq +=1
                print("secuencia: ", new_socket.seq)
                print("conexion establecida con exito")
                return new_socket, new_address
                
            else:
                new_socket.socket.sendto(syn_ack_seg.encode(), client_address)
                print("Reenviando mensaje: ", syn_ack_seg)
    
    
    def send(self, message):
        self.panic_button = 10
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
        if self.debug: print("Enviando mensaje: ", segment)      
        while True:           
            try:
                ack_msg, _ = self.socket.recvfrom(23)
                response = self.parse_segment(ack_msg.decode())
                if response["ACK"] and response["SEQ"] == (self.seq + len(length)):
                    if self.debug: print("largo recivido ", length)
                    self.seq += len(segment["DATA"])         
                    break
                elif response["ACK"] and response["SYN"] and response["SEQ"] == self.seq-1:
                    ack_response = {"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq, "DATA":None}
                    self.socket.sendto(self.create_segment(ack_response).encode(), self.address_destiny)
                    if self.debug: print("Enviando mensaje: ", ack_response)
               
            except socket.timeout:
                self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
                if self.debug: print("reenviando mensaje: ", segment)    
                if self.debug: print("largo enviado nuevamente")
                
        
        while cont < len(msg):
            segment = {"SYN":False, "ACK":False, "FIN":False, "SEQ":self.seq ,"DATA":None}
            segment["DATA"] = msg[cont]
            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
            if self.debug: print("Enviando Mensaje:  ", segment)
            
            try:
                ack_msg, _ = self.socket.recvfrom(23)
                response = self.parse_segment(ack_msg.decode())
                if response["ACK"] and response["SEQ"]== (self.seq + len(msg[cont])):
                    print("confirmacion recibida")
                    self.seq += len(msg[cont])
                    cont+=1
                
            except socket.timeout:
                pass
                
        print("mensaje enviado")
              
    def recv(self, buff_size: int):
        self.panic_button = 10
        print("esperando mensaje")
        full_msg = ""
        self.socket.settimeout(self.timeout)
        segment = {"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq,"DATA":None}

        if self.msg_left == 0 and self.msg_buff == []:
            while True:
                try:
                    msg, _ = self.socket.recvfrom(23+buff_size)
                    header = self.parse_segment(msg.decode())
                    if header["DATA"] is not None:
                        if header["SEQ"] + len(header["DATA"]) > self.seq and self.seq == header["SEQ"]:
                            self.msg_left = int(header["DATA"])
                            self.seq += len(header["DATA"])
                            segment["SEQ"] = self.seq
                            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
                            if self.debug: print("Enviando mensaje: ", segment)
                            print("largo del mensaje recibido: ", self.msg_left)
                            break
                        else:
                            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
                            if self.debug: print("Enviando mensaje: ", segment)
                            
                            
                except socket.timeout:
                    pass
        if self.debug: print("quedan por recibir: ", self.msg_left)
        if self.msg_buff != []:
            current_msg_size = len(full_msg)
            full_msg += self.msg_buff[0][:(buff_size - current_msg_size)]
            self.msg_left -= len(self.msg_buff[0][:(buff_size - current_msg_size)])
            self.seq += len(self.msg_buff[0][:(buff_size - current_msg_size)])
            segment["SEQ"] = self.seq
            if self.debug: print("Enviando mensaje: ", segment)
            if self.debug: print("mensaje recivido hasta ahora: ", full_msg)
            if self.debug: print("quedan por recibir: ", self.msg_left)
            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
            if len(full_msg) == buff_size:
                if self.msg_left != 0:
                    self.msg_buff = [self.msg_buff[0][(buff_size - current_msg_size):]]
                else:
                    self.msg_buff = []
                return full_msg.encode()
            
            self.msg_buff = []
        while self.msg_left > 0:
            try:
                msg, _ = self.socket.recvfrom(23+self.msg_left)
                header = self.parse_segment(msg.decode())
                if self.debug: print("Mensaje recibido: ", header)
                if header["DATA"] is not None:
                    if header["SEQ"] + len(header["DATA"]) > self.seq and self.seq == header["SEQ"]:
                        current_msg_size = len(full_msg)
                        full_msg += header["DATA"][:(buff_size - current_msg_size)]
                        self.msg_left -= len(header["DATA"][:(buff_size - current_msg_size)])
                        self.seq += len(header["DATA"][:(buff_size - current_msg_size)])
                        segment["SEQ"] = self.seq
                        if self.debug: print("Enviando mensaje: ", segment)
                        if self.debug: print("mensaje recivido hasta ahora: ", full_msg)
                        if self.debug: print("quedan por recibir: ", self.msg_left)
                        self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
                        if len(full_msg) == buff_size:
                            if self.msg_left != 0:
                                self.msg_buff = [header["DATA"][(buff_size - current_msg_size):]]
                                if self.debug: print("guardando en buffer: ", self.msg_buff)
                            break 
                        
                    
                        
                    else:
                        
                        self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
                        if self.debug: print("Enviando mensaje: ", segment)
                        
            except socket.timeout:
                self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny)
                if self.debug: print("Enviando mensaje: ", segment)
                
        
        print("mensaje completo recibido: ", full_msg)
        

        return full_msg.encode()

    def close(self):
        print("cerrando conexion")
        self.socket.settimeout(self.timeout)
        self.socket.sendto(self.create_segment({"SYN":False, "ACK":False, "FIN":True, "SEQ":self.seq, "DATA":None}).encode(), self.address_destiny)
        if self.debug: print("Enviando mensaje: ", {"SYN":False, "ACK":False, "FIN":True, "SEQ":self.seq, "DATA":None})
        tries = 3
        while tries > 0:
            while True:
                try:
                    end_message,_ = self.socket.recvfrom(23)
                    break
                except socket.timeout:
                    tries -= 1
                    self.socket.settimeout(self.timeout)
                    self.socket.sendto(self.create_segment({"SYN":False, "ACK":False, "FIN":True, "SEQ":self.seq, "DATA":None}).encode(), self.address_destiny)
                    if self.debug: print("Reenviando mensaje: ", {"SYN":False, "ACK":False, "FIN":True, "SEQ":self.seq, "DATA":None})
                    if tries == 0:
                        self.socket.close()
                        print("conexion terminada por tiempo de espera acabado")
                        return

            end_header = self.parse_segment(end_message.decode())
            if end_header["FIN"] and end_header["ACK"] and (end_header["SEQ"] == self.seq+1):
                self.seq += 1
                self.socket.sendto(self.create_segment({"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq+1, "DATA":None}).encode(), self.address_destiny)
                if self.debug: print("Enviando mensaje: ", {"SYN":False, "ACK":False, "FIN":True, "SEQ":self.seq+1, "DATA":None})
                self.socket.close()
                print("conexion terminada con exito")
                return
        self.socket.close()
        print("conexion terminada por tiempo de espera acabado")
        return

    def recv_close(self):
        print("esperando cierre de conexion")
        self.socket.settimeout(self.timeout)
        while True:
            while True:
                try:
                    end_message, addr = self.socket.recvfrom(23)
                    break
                except socket.timeout:
                    
                    pass
            end_header = self.parse_segment(end_message.decode())
            if end_header["FIN"] and end_header["SEQ"] == self.seq:
                self.seq += 1
                self.socket.sendto(self.create_segment({"SYN":False, "ACK":True, "FIN":True, "SEQ":self.seq, "DATA":None}).encode(), addr)
                if self.debug: print("Enviando mensaje: ", {"SYN":False, "ACK":True, "FIN":True, "SEQ":self.seq, "DATA":None})
                tries = 3
                self.socket.settimeout(self.timeout)
                while tries > 0:
                    while True:
                        try:
                            end_message, addr = self.socket.recvfrom(23)
                            break
                        except socket.timeout:
                            tries -= 1
                            self.socket.settimeout(self.timeout)
                            self.socket.sendto(self.create_segment({"SYN":False, "ACK":True, "FIN":True, "SEQ":self.seq, "DATA":None}).encode(), addr)
                            if self.debug: print("Enviando mensaje: ", {"SYN":False, "ACK":True, "FIN":True, "SEQ":self.seq, "DATA":None})
                            if tries == 0:
                                self.socket.close()
                                print("conexion terminada por tiempo de espera acabado")
                                return
                    end_header = self.parse_segment(end_message.decode())
                    if end_header["ACK"] and end_header["SEQ"] == self.seq+1:
                        self.socket.close()
                        print("conexion terminada con exito")
                        return
                return
