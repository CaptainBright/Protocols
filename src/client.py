import socket
from rdt import RDT_send, UnreliableChannel, generate_random_data


def main() -> None:
    server_addr = ("127.0.0.1", 9000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    channel = UnreliableChannel(loss_rate=0.2, corrupt_rate=0.1)
    data = generate_random_data(40)
    print(f"Client generated data: {data}")
    RDT_send(sock, server_addr, data, channel)


if __name__ == "__main__":
    main()
