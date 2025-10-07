import CongestionControl as cc


# tests
def initialization_test(congestion_controler, MSS):
    if congestion_controler.get_cwnd() == MSS and congestion_controler.get_MSS_in_cwnd() == 1 \
            and congestion_controler.get_ssthresh() is None and congestion_controler.is_state_slow_start(): print("Initial test passed")
    else: print("Initial test failed")


def ack_test(congestion_controler, MSS):
    for i in range(3):
        for j in range(congestion_controler.get_MSS_in_cwnd()):
            congestion_controler.event_ack_received()

    if congestion_controler.get_cwnd() == 8*MSS and congestion_controler.get_MSS_in_cwnd() == 8: print("ACK test passed")
    else: print("ACK test failed")


def timeout_test(congestion_controler, MSS):
    congestion_controler.event_timeout()
    if congestion_controler.get_cwnd() == MSS and congestion_controler.get_MSS_in_cwnd() == 1 \
            and congestion_controler.is_state_slow_start() and congestion_controler.get_ssthresh() == 4 * MSS: print("Timeout test passed")
    else: print("Timeout test failed")


def ssthresh_test(congestion_controler, MSS):
    for i in range(3):
        for j in range(congestion_controler.get_MSS_in_cwnd()):
            congestion_controler.event_ack_received()
    if congestion_controler.is_state_congestion_avoidance() and congestion_controler.get_cwnd() == 5*MSS  \
            and congestion_controler.get_MSS_in_cwnd() == 5: print("ssthresh test passed")
    else: print("ssthresh test failed")


def timeout_in_congestion_avoidance_test(congestion_controler, MSS):
    congestion_controler.event_timeout()
    if congestion_controler.is_state_slow_start() and congestion_controler.get_cwnd() == MSS and congestion_controler.get_MSS_in_cwnd() == 1 \
            and congestion_controler.get_ssthresh() == int(5/2*MSS): print("Timeout test 2 passed")
    else: print("Timeout test 2 failed")

# Ejecute este test
def congestion_control_object_test(MSS):
    congestion_controler = cc.CongestionControl(MSS)
    initialization_test(congestion_controler, MSS)
    ack_test(congestion_controler, MSS)
    timeout_test(congestion_controler, MSS)
    ssthresh_test(congestion_controler, MSS)
    timeout_in_congestion_avoidance_test(congestion_controler, MSS)

MSS = 7
congestion_control_object_test(MSS)