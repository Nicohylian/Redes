import socket

class SocketTCP:
    def __init__(self):
        self.socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address_origin=None
        self.addres_destiny=None
        self.timeout=0.5
        
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