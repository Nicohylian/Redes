from socketUDP import SocketUDP 
import CongestionControl as cc
import random
import slidingWindowCC as sw
import time

class SocketTCP:
    def __init__(self):
        self.debug = False
        self.socket= SocketUDP()
        self.address_origin=None
        self.address_destiny=None
        self.timeout=5.0
        self.seq:int =0
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
        self.socket.sendto(syn_segment.encode(), address, timer_index=0)
        if self.debug: print("Enviando mensaje: ", syn_segment)
        while True:
            while True:
                try:
                    message, new_address = self.socket.recvfrom(23)
                    break
                except TimeoutError:
                    self.socket.sendto(syn_segment.encode(), address, timer_index=0)
                    if self.debug: print("Reenviando mensaje: ", syn_segment)
                    
            header = self.parse_segment(message.decode())
            
            if (header["SYN"] and header["ACK"] and header["SEQ"]==self.seq +1):
                self.socket.stop_timer(timer_index=0)
                self.seq +=2
                self.address_destiny = new_address
                print("Direccion del servidor: ", self.address_destiny)
                ack_segment = self.create_segment({"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq, "DATA":None})
                self.socket.sendto(ack_segment.encode(), self.address_destiny, timer_index=0)
                if self.debug: print("Enviando mensaje: ", ack_segment)
                break
            else:
                self.socket.sendto(syn_segment.encode(), address, timer_index=0)
                if self.debug: print("Reenviando mensaje: ", syn_segment)

        
        print("Conexion establecida con exito")
        print("secuencia: ", self.seq)
        return

            
    def accept(self):
        self.socket.settimeout(self.timeout)
        while True:
            while True:
                try:
                    message, client_address = self.socket.recvfrom(23)
                    header = self.parse_segment(message.decode())
                    break
                except TimeoutError:
                    pass
            if header["SYN"]:
                break

        self.address_destiny = client_address
        self.seq = header["SEQ"]+1
        
        new_socket = SocketTCP()
        if self.debug: new_socket.debug = True
        new_address = (self.address_origin[0], self.address_origin[1]+self.seq)
        print("nueva direccion del servidor: ", new_address)
        new_socket.bind(new_address)
        new_socket.address_destiny = self.address_destiny
        new_socket.seq = self.seq
        new_socket.socket.settimeout(self.timeout)
        syn_ack_seg = self.create_segment({"SYN":True, "ACK":True, "FIN":False, "SEQ":self.seq,"DATA":None})
        new_socket.socket.sendto(syn_ack_seg.encode(), client_address, timer_index=0)
        if self.debug: print("Enviando mensaje: ", syn_ack_seg)
        while True:
            while True:
                try:
                    ack_msg, _ = new_socket.socket.recvfrom(23)
                    break
                except TimeoutError:
                    new_socket.socket.settimeout(self.timeout)
                    new_socket.socket.sendto(syn_ack_seg.encode(), client_address, timer_index=0)
                    if self.debug: print("Reenviando mensaje: ", syn_ack_seg)
            ack_header = self.parse_segment(ack_msg.decode())
            if ack_header["ACK"] and ack_header["SEQ"]==self.seq + 1:
                new_socket.socket.stop_timer(timer_index=0)
                new_socket.seq +=1
                print("conexion establecida con exito")
                print("secuencia: ", new_socket.seq)
                return new_socket, new_address
                
            else:
                new_socket.socket.sendto(syn_ack_seg.encode(), client_address, timer_index=0)
                if self.debug: print("Reenviando mensaje: ", syn_ack_seg)
    
    def send_using_stop_and_wait(self, message):
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
         
        self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
        if self.debug: print("Enviando mensaje: ", segment) 
        while True:           
            try:
                ack_msg, _ = self.socket.recvfrom(23)
                response = self.parse_segment(ack_msg.decode())
                if self.debug: print("mensaje de confirmacion recivido: ", response)
                if response["ACK"] and response["SEQ"] == (self.seq + len(length)):
                    self.socket.stop_timer(timer_index=0)
                    print("largo del mensaje recivido: ", length)
                    self.seq += len(segment["DATA"])         
                    break
                elif response["ACK"] and response["SYN"] and response["SEQ"] == self.seq-1:
                    ack_response = {"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq, "DATA":None}
                    self.socket.sendto(self.create_segment(ack_response).encode(), self.address_destiny, timer_index=0)
                    if self.debug: print("Enviando mensaje: ", ack_response)
               
            except TimeoutError:
                self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                if self.debug: print("reenviando mensaje: ", segment)    
                print("largo enviado nuevamente")
                
        
        while cont < len(msg):
            segment = {"SYN":False, "ACK":False, "FIN":False, "SEQ":self.seq ,"DATA":None}
            segment["DATA"] = msg[cont]
            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
            if self.debug: print("dato enviado ", msg[cont])
            
            try:
                ack_msg, _ = self.socket.recvfrom(23)
                response = self.parse_segment(ack_msg.decode())
                if self.debug: print("mensaje de confirmacion recivido: ", response)
                if response["ACK"] and response["SEQ"]== (self.seq + len(msg[cont])):
                    self.socket.stop_timer(timer_index=0)
                    print("confirmacion recibida")
                    self.seq += len(msg[cont])
                    cont+=1
                
            except TimeoutError:
                pass
                
        print("mensaje enviado")

    def send_using_go_back_n(self, message):
        congestion_controler: CongestionControl = cc.CongestionControl(8)
        length = str(len(message)).encode()
        initial_seq = self.seq
        msg = []
        window_size = congestion_controler.get_MSS_in_cwnd()

        for i in range(0, len(message), congestion_controler.MSS):
            msg.append(message[i:i+congestion_controler.MSS])

        data_to_send = sw.SlidingWindowCC(congestion_controler.get_MSS_in_cwnd(), [length]+msg, initial_seq)
        if self.debug: print(data_to_send)
        if self.debug: print("tamaño de ventana: ", data_to_send.window_size)
        current_data = []
        current_seq = []
        segments = []
        self.socket.settimeout(self.timeout)
        current_size = min(congestion_controler.get_MSS_in_cwnd(), len([length]+msg))
        for i in range(current_size):
            data= data_to_send.get_data((i))
            if data is not None:
                current_data.append(data_to_send.get_data(i))
                current_seq.append(data_to_send.get_sequence_number(i))
                segments.append({"SYN":False, "ACK":False, "FIN":False, "SEQ":current_seq[i],"DATA":current_data[i].decode()})
                self.socket.sendto(self.create_segment(segments[i]).encode(), self.address_destiny, timer_index=0)
                if self.debug: print("Enviando mensaje: ", segments[i])
          
            
            
        
        ind = None
        while len(current_data) > 0:
            try:
                ack_message, _ = self.socket.recvfrom(23)
                response = self.parse_segment(ack_message.decode())
                if self.debug: print("mensaje de confirmacion recibido: ",response)
                if response["SYN"] and response["ACK"] and response["SEQ"] == self.seq-1:
                    ack_response = {"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq, "DATA":None}
                    self.socket.sendto(self.create_segment(ack_response).encode(), self.address_destiny, timer_index=0)
                    if self.debug: print("Enviando mensaje: ", ack_response)
                else:
                    for segment in segments:
                        if response["ACK"] and response["SEQ"] == (segment["SEQ"] + len(segment["DATA"])) and ind is None:
                            congestion_controler.event_ack_received()
                            if congestion_controler.is_state_slow_start():
                                window_size = congestion_controler.get_MSS_in_cwnd()
                                data_to_send.update_window_size(congestion_controler.get_MSS_in_cwnd())
                                if self.debug: print(data_to_send)
                                new_data = data_to_send.get_data(congestion_controler.get_MSS_in_cwnd()-1)
                                if new_data is not None:
                                    current_data.append(new_data)
                                    new_seq = data_to_send.get_sequence_number(congestion_controler.get_MSS_in_cwnd()-1)
                                    current_seq.append(new_seq)
                                    segments.append({"SYN":False, "ACK":False, "FIN":False, "SEQ":new_seq,"DATA":new_data.decode()})
                                    self.socket.sendto(self.create_segment({"SYN":False, "ACK":False, "FIN":False, "SEQ":new_seq,"DATA":new_data.decode()}).encode(), self.address_destiny, timer_index=0)

                            elif congestion_controler.is_state_congestion_avoidance:
                                if window_size != congestion_controler.get_MSS_in_cwnd():
                                    window_size = congestion_controler.get_MSS_in_cwnd()
                                    data_to_send.update_window_size(congestion_controler.get_MSS_in_cwnd())
                                    if self.debug: print(data_to_send)
                                    new_data = data_to_send.get_data(congestion_controler.get_MSS_in_cwnd()-1)
                                    if new_data is not None:
                                        current_data.append(new_data)
                                        new_seq = data_to_send.get_sequence_number(congestion_controler.get_MSS_in_cwnd()-1)
                                        current_seq.append(new_seq)
                                        segments.append({"SYN":False, "ACK":False, "FIN":False, "SEQ":new_seq,"DATA":new_data.decode()})
                                        self.socket.sendto(self.create_segment({"SYN":False, "ACK":False, "FIN":False, "SEQ":new_seq,"DATA":new_data.decode()}).encode(), self.address_destiny, timer_index=0)
                            print("confirmacion recibida")
                            ind = segments.index(segment)
                            data_to_send.move_window(ind+1)
                            if self.debug: print(data_to_send)
                            i = 0
                            while i <= ind:
                                current_data.pop(0)
                                current_seq.pop(0)
                                i+=1
                            for j in range(congestion_controler.get_MSS_in_cwnd()-(ind+1), congestion_controler.get_MSS_in_cwnd()):
                                data = data_to_send.get_data(j)
                                if data is not None: 
                                    current_data.append(data)
                                    seq = data_to_send.get_sequence_number(j)
                                    current_seq.append(seq)
                                    segments.append({"SYN":False, "ACK":False, "FIN":False, "SEQ": seq, "DATA": data.decode()})
                            self.seq = (segment["SEQ"] + len(segment["DATA"]))
                            break
                    while (segments[-1]["SEQ"] + len(segments[-1]["DATA"])) < response["SEQ"] and response["ACK"] and ind is None:
                        data_to_send.move_window(window_size)
                        if self.debug: print(data_to_send)
                        current_data.clear()
                        current_seq.clear()
                        segments.clear()
                        for i in range(window_size):
                            data= data_to_send.get_data((i))
                            if data is not None:
                                current_data.append(data_to_send.get_data(i))
                                current_seq.append(data_to_send.get_sequence_number(i))
                                segments.append({"SYN":False, "ACK":False, "FIN":False, "SEQ":current_seq[i],"DATA":current_data[i].decode()})
                                self.socket.sendto(self.create_segment(segments[i]).encode(), self.address_destiny, timer_index=0)
                                if self.debug: print("Enviando mensaje: ", segments[i])
                    for segment in segments:
                        if response["ACK"] and response["SEQ"] == (segment["SEQ"] + len(segment["DATA"])) and ind is None:
                            congestion_controler.event_ack_received()
                            if congestion_controler.is_state_slow_start():
                                window_size = congestion_controler.get_MSS_in_cwnd()
                                data_to_send.update_window_size(congestion_controler.get_MSS_in_cwnd())
                                if self.debug: print(data_to_send)
                                new_data = data_to_send.get_data(congestion_controler.get_MSS_in_cwnd()-1)
                                if new_data is not None:
                                    current_data.append(new_data)
                                    new_seq = data_to_send.get_sequence_number(congestion_controler.get_MSS_in_cwnd()-1)
                                    current_seq.append(new_seq)
                                    segments.append({"SYN":False, "ACK":False, "FIN":False, "SEQ":new_seq,"DATA":new_data.decode()})
                                    self.socket.sendto(self.create_segment({"SYN":False, "ACK":False, "FIN":False, "SEQ":new_seq,"DATA":new_data.decode()}).encode(), self.address_destiny, timer_index=0)
                            elif congestion_controler.is_state_congestion_avoidance:
                                if window_size != congestion_controler.get_MSS_in_cwnd():
                                    window_size = congestion_controler.get_MSS_in_cwnd()
                                    data_to_send.update_window_size(congestion_controler.get_MSS_in_cwnd())
                                    if self.debug: print(data_to_send)
                                    new_data = data_to_send.get_data(congestion_controler.get_MSS_in_cwnd()-1)
                                    if new_data is not None:
                                        current_data.append(new_data)
                                        new_seq = data_to_send.get_sequence_number(congestion_controler.get_MSS_in_cwnd()-1)
                                        current_seq.append(new_seq)
                                        segments.append({"SYN":False, "ACK":False, "FIN":False, "SEQ":new_seq,"DATA":new_data.decode()})
                                        self.socket.sendto(self.create_segment({"SYN":False, "ACK":False, "FIN":False, "SEQ":new_seq,"DATA":new_data.decode()}).encode(), self.address_destiny, timer_index=0)
                            print("confirmacion recibida")
                            ind = segments.index(segment)
                            data_to_send.move_window(ind+1)
                            if self.debug: print(data_to_send)
                            i = 0
                            while i <= ind:
                                current_data.pop(0)
                                current_seq.pop(0)
                                i+=1
                            for j in range(congestion_controler.get_MSS_in_cwnd()-(ind+1), congestion_controler.get_MSS_in_cwnd()):
                                data = data_to_send.get_data(j)
                                if data is not None: 
                                    current_data.append(data)
                                    seq = data_to_send.get_sequence_number(j)
                                    current_seq.append(seq)
                                    segments.append({"SYN":False, "ACK":False, "FIN":False, "SEQ": seq, "DATA": data.decode()})
                            self.seq = (segment["SEQ"] + len(segment["DATA"]))
                            
                            break

            except TimeoutError:
                congestion_controler.event_timeout()
                i = congestion_controler.get_MSS_in_cwnd()
                while i != len(segments) and i < len(segments):
                    current_data.pop(-1)
                    current_seq.pop(-1)
                    segments.pop(-1)
                window_size = congestion_controler.get_MSS_in_cwnd()
                data_to_send.update_window_size(congestion_controler.get_MSS_in_cwnd())
                if self.debug: print(data_to_send)
                for segment in segments:
                    self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                    if self.debug: print("Enviando mensaje: ", segment)
            
            if ind is not None:
                i = 0
                while i <= ind:
                    segments.pop(0)
                    i+=1
                print(segments)
                for i in range(ind+1, len(segments)):
                    self.socket.sendto(self.create_segment(segments[i]).encode(), self.address_destiny, timer_index=0)
                    if self.debug: print("Enviando mensaje: ", segments[i])
                    
                ind = None
        print("mensaje enviado")







    def send(self, message, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        elif mode == "go_back_n":
            self.send_using_go_back_n(message)
        
    def recv_using_stop_and_wait(self, buff_size: int):
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
                            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                            if self.debug: print("Enviando mensaje: ", segment)
                            print("largo del mensaje recibido: ", self.msg_left)
                            break
                        else:
                            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                            if self.debug: print("Enviando mensaje: ", segment)
                            
                except TimeoutError:
                    self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                    if self.debug: print("Enviando mensaje: ", segment)
        
        if self.debug: print("quedan por recibir: ", self.msg_left)
        print("Estado buffer: ", self.msg_buff)
        if self.msg_buff != []:
            current_msg_size = len(full_msg)
            full_msg += self.msg_buff[0][:(buff_size - current_msg_size)]
            self.msg_left -= len(self.msg_buff[0][:(buff_size - current_msg_size)])
            self.seq += len(self.msg_buff[0][:(buff_size - current_msg_size)])
            segment["SEQ"] = self.seq
            if self.debug: print("Enviando mensaje: ", segment)
            if self.debug: print("mensaje recivido hasta ahora: ", full_msg)
            if self.debug: print("quedan por recibir: ", self.msg_left)
            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
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
                
                if header["DATA"] is not None:
                    if header["SEQ"] + len(header["DATA"]) > self.seq and self.seq == header["SEQ"]:
                        current_msg_size = len(full_msg)
                        full_msg += header["DATA"][:(buff_size - current_msg_size)]
                        self.msg_left -= len(header["DATA"][:(buff_size - current_msg_size)])
                        self.seq += len(header["DATA"][:(buff_size - current_msg_size)])
                        segment["SEQ"] = self.seq
                        if self.debug: print("mensaje recivido hasta ahora: ", full_msg)
                        if self.debug: print("quedan por recibir: ", self.msg_left)
                        self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                        if self.debug: print("Enviando mensaje: ", segment)
                        if len(full_msg) == buff_size:
                            if self.msg_left != 0:
                                self.msg_buff = [header["DATA"][(buff_size - current_msg_size):]]
                                if self.debug: print("guardando en buffer: ", self.msg_buff)
                            break 
                        
                    
                        
                    else:
                        
                        self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                        if self.debug: print("Enviando mensaje: ", segment)
                        
            except TimeoutError:
                self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                if self.debug: print("Enviando mensaje: ", segment)
        
        print("mensaje completo recibido: ", full_msg)
        

        return full_msg.encode()


    def recv_using_go_back_n(self, buff_size: int):
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
                    if self.debug: print("Mensaje recibido: ", header)
                    if header["DATA"] is not None:
                        if header["SEQ"] + len(header["DATA"]) > self.seq and self.seq == header["SEQ"]:
                            self.msg_left = int(header["DATA"])
                            print("largo del mensaje recibido: ", self.msg_left)
                            self.seq += len(header["DATA"])
                            segment["SEQ"] = self.seq
                            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                            if self.debug: print("Enviando mensaje: ", segment)
                            
                            break
                        else:
                            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                            if self.debug: print("Enviando mensaje: ", segment)
                            
                            
                except TimeoutError:
                    self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                    if self.debug: print("Enviando mensaje: ", segment)
        
        if self.msg_buff != []:
            current_msg_size = len(full_msg)
            full_msg += self.msg_buff[0][:(buff_size - current_msg_size)]
            self.msg_left -= len(self.msg_buff[0][:(buff_size - current_msg_size)])
            self.seq += len(self.msg_buff[0][:(buff_size - current_msg_size)])
            segment["SEQ"] = self.seq
            if self.debug: print("Enviando mensaje: ", segment)
            self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
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
                        self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                        if len(full_msg) == buff_size:
                            if self.msg_left != 0:
                                self.msg_buff = [header["DATA"][(buff_size - current_msg_size):]]
                                if self.debug: print("guardando en buffer: ", self.msg_buff)
                            break           
                    else:
                        
                        self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                        if self.debug: print("Enviando mensaje: ", segment)
                        
            except TimeoutError:
                self.socket.sendto(self.create_segment(segment).encode(), self.address_destiny, timer_index=0)
                if self.debug: print("Enviando mensaje: ", segment)
        
        print("mensaje completo recibido: ", full_msg)
        

        return full_msg.encode()


    def recv(self, buff_size: int, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)

        

    def close(self):
        print("cerrando conexion")
        self.socket.settimeout(self.timeout)
        self.socket.sendto(self.create_segment({"SYN":False, "ACK":False, "FIN":True, "SEQ":self.seq, "DATA":None}).encode(), self.address_destiny, timer_index=0)
        
        tries = 3
        while tries > 0:
            while True:
                try:
                    end_message,_ = self.socket.recvfrom(23)
                    break
                except TimeoutError:
                    tries -= 1
                    self.socket.settimeout(self.timeout)
                    self.socket.sendto(self.create_segment({"SYN":False, "ACK":False, "FIN":True, "SEQ":self.seq, "DATA":None}).encode(), self.address_destiny, timer_index=0)
                    if tries < 0:
                        self.socket.close()
                        print("conexion terminada por tiempo de espera acabado")
                        return

            end_header = self.parse_segment(end_message.decode())
            if end_header["FIN"] and end_header["ACK"] and (end_header["SEQ"] == self.seq+1):
                self.socket.stop_timer(timer_index=0)
                self.seq += 1
                tries = 2
                self.socket.sendto(self.create_segment({"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq+1, "DATA":None}).encode(), self.address_destiny, timer_index=0)
                while tries > 0:
                    try:
                        self.socket.recvfrom(23)
                    except TimeoutError:
                        tries-=1
                        self.socket.sendto(self.create_segment({"SYN":False, "ACK":True, "FIN":False, "SEQ":self.seq+1, "DATA":None}).encode(), self.address_destiny, timer_index=0)
                
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
                except TimeoutError:
                    pass
            end_header = self.parse_segment(end_message.decode())
            if end_header["FIN"] and end_header["SEQ"] == self.seq:
                self.seq += 1
                self.socket.settimeout(self.timeout)
                self.socket.sendto(self.create_segment({"SYN":False, "ACK":True, "FIN":True, "SEQ":self.seq, "DATA":None}).encode(), addr, timer_index=0)
                tries = 3
                
                while tries > 0:
                    while True:
                        try:
                            end_message, addr = self.socket.recvfrom(23)
                            break
                        except TimeoutError:
                            tries -= 1
                            self.socket.settimeout(self.timeout)
                            self.socket.sendto(self.create_segment({"SYN":False, "ACK":True, "FIN":True, "SEQ":self.seq, "DATA":None}).encode(), addr, timer_index=0)
                            if tries == 0:
                                self.socket.close()
                                print("conexion terminada por tiempo de espera acabado")
                                return
                    end_header = self.parse_segment(end_message.decode())
                    if end_header["ACK"] and end_header["SEQ"] == self.seq+1:
                        self.socket.stop_timer(timer_index=0)
                        self.socket.close()
                        print("conexion terminada con exito")
                        return
                self.socket.close()
                print("conexion terminada por tiempo de espera acabado")
                return
