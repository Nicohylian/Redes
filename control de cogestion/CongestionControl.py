

class CongestionControl:
    def __init__(self, MSS: int):
        self.current_state = "Slow Start"
        self.MSS: int = MSS
        self.cwnd: float = MSS
        self.ssthresh: int = None
        self.ack_repeated = -1
        self.first_timeout = True
        
        

    def get_cwnd(self):
        return int(self.cwnd)
    
    def get_MSS_in_cwnd(self):
        return int(self.cwnd // self.MSS)
    
    def event_ack_received(self):
        if self.current_state == "Slow Start":
            self.cwnd = int(self.cwnd) + self.MSS
            if self.ssthresh is not None and self.get_cwnd() >= self.ssthresh:
                self.current_state = "Congestion Avoidance"
        elif self.current_state == "Congestion Avoidance":
            self.cwnd = self.cwnd + (1/self.get_MSS_in_cwnd())*self.MSS
        elif self.current_state == "Fast Recovery":
            if self.current_ack_received == self.last_ack_received:
                self.cwnd = int(self.cwnd) + self.MSS*self.ack_repeated

    def event_timeout(self):
        self.ssthresh = self.get_cwnd() // 2
        self.cwnd = self.MSS
        

        if self.first_timeout and self.current_state == "Slow Start":
            self.first_timeout = False
            if self.ssthresh <= self.get_cwnd():
                self.current_state = "Congestion Avoidance"
        else:
            self.current_state = "Slow Start"


        
        
        

    def is_state_slow_start(self):
        return self.current_state == "Slow Start"
    
    def is_state_congestion_avoidance(self):
        return self.current_state == "Congestion Avoidance"
    
    def get_ssthresh(self):
        return self.ssthresh