import socket
from rdt import RDT_recv, UnreliableChannel, UDT_recv


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", 9000))
    channel = UnreliableChannel(loss_rate=0.0, corrupt_rate=0.0)
    expected_seq = 0
    received = 0
    while received < 10:
        packet, addr = UDT_recv(sock)
        data, expected_seq = RDT_recv(sock, packet, addr, expected_seq, channel)
        if data:
            received += 1


if __name__ == "__main__":
    main()
