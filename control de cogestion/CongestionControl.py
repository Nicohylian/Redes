from slidingWindowCC import SlidingWindowCC
from socketUDP import SocketUDP

class CongestionControl:
    def __init__(self, MSS: int):
        self.current_state = "Slow Start"
        self.MSS: bytes = MSS
        self.cwnd: bytes = MSS
        self.ssthresh: int = None
        self.ack_repeated = -1
        self.first_timeout = True
        
        

    def get_cwnd(self):
        return int(float(self.cwnd)//1)
    
    def get_MSS_in_cwnd(self):
        return int(float(self.cwnd) // self.MSS)
    
    def event_ack_received(self):
        if self.current_state == "Slow Start":
            self.cwnd = str(int(self.cwnd) + self.MSS)
            if self.ssthresh is not None and self.get_cwnd() >= self.ssthresh:
                self.current_state = "Congestion Avoidance"
        elif self.current_state == "Congestion Avoidance":
            self.cwnd = str(float(self.cwnd) + (1/self.get_MSS_in_cwnd())*self.MSS)
        elif self.current_state == "Fast Recovery":
            if self.current_ack_received == self.last_ack_received:
                self.cwnd = str(int(self.cwnd) + self.MSS*self.ack_repeated)

    def event_timeout(self):
        if self.first_timeout and self.current_state == "Slow Start":
            self.ssthresh = int(self.cwnd)//2
            self.cwnd = str(self.MSS)
            self.first_timeout = False
            if self.ssthresh <= self.get_cwnd():
                self.current_state = "Congestion Avoidance"


        else:
            self.ssthresh = self.get_cwnd() // 2
            self.cwnd = str(self.MSS)
            self.current_state = "Slow Start"
        

    def is_state_slow_start(self):
        return self.current_state == "Slow Start"
    
    def is_state_congestion_avoidance(self):
        return self.current_state == "Congestion Avoidance"
    
    def get_ssthresh(self):
        return self.ssthresh