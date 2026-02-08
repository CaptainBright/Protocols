import random
import socket
import struct
import time
from dataclasses import dataclass
from typing import Optional, Tuple

WINDOW_SIZE = 3
SEQ_MOD = WINDOW_SIZE + 1
DATA_SIZE = 4
FLAG_DATA = 1
FLAG_ACK = 2


def compute_checksum(payload: bytes) -> int:
    return sum(payload) % 65536


def build_packet(flag: int, seq: int, data: bytes) -> bytes:
    if len(data) != DATA_SIZE:
        raise ValueError("Data payload must be 4 bytes")
    header = data + struct.pack("!BB", seq, flag)
    checksum = compute_checksum(header)
    return header + struct.pack("!H", checksum)


def parse_packet(packet: bytes) -> Tuple[bytes, int, int, int]:
    if len(packet) != DATA_SIZE + 1 + 1 + 2:
        raise ValueError("Invalid packet length")
    data = packet[:DATA_SIZE]
    seq, flag = struct.unpack("!BB", packet[DATA_SIZE:DATA_SIZE + 2])
    checksum = struct.unpack("!H", packet[DATA_SIZE + 2:])[0]
    return data, seq, flag, checksum


def is_corrupt(packet: bytes) -> bool:
    data, seq, flag, checksum = parse_packet(packet)
    header = data + struct.pack("!BB", seq, flag)
    return compute_checksum(header) != checksum


@dataclass
class UnreliableChannel:
    loss_rate: float = 0.1
    corrupt_rate: float = 0.1
    drop_every: Optional[int] = None
    _counter: int = 0

    def introduce_error(self, packet: bytes) -> Optional[bytes]:
        self._counter += 1
        if self.drop_every and self._counter % self.drop_every == 0:
            return None
        if random.random() < self.loss_rate:
            return None
        if random.random() < self.corrupt_rate:
            index = random.randint(0, len(packet) - 1)
            corrupted = bytearray(packet)
            corrupted[index] ^= 0xFF
            return bytes(corrupted)
        return packet


def UDT_send(sock: socket.socket, addr: Tuple[str, int], packet: bytes, channel: UnreliableChannel) -> None:
    maybe_packet = channel.introduce_error(packet)
    if maybe_packet is None:
        print("UDT_send: packet lost")
        return
    sock.sendto(maybe_packet, addr)


def UDT_recv(sock: socket.socket, buffer_size: int = 1024) -> Tuple[bytes, Tuple[str, int]]:
    data, addr = sock.recvfrom(buffer_size)
    return data, addr


def RDT_send(
    sock: socket.socket,
    addr: Tuple[str, int],
    data: bytes,
    channel: UnreliableChannel,
    timeout: float = 0.5,
    window_size: int = WINDOW_SIZE,
) -> None:
    if len(data) % DATA_SIZE != 0:
        raise ValueError("Data length must be multiple of 4")
    chunks = [data[i:i + DATA_SIZE] for i in range(0, len(data), DATA_SIZE)]
    total_packets = len(chunks)
    base = 0
    next_seq = 0

    sock.settimeout(timeout)

    while base < total_packets:
        while next_seq < base + window_size and next_seq < total_packets:
            seq = next_seq % SEQ_MOD
            packet = build_packet(FLAG_DATA, seq, chunks[next_seq])
            print(f"RDT_send: sending seq={seq} data={chunks[next_seq]}")
            UDT_send(sock, addr, packet, channel)
            next_seq += 1

        try:
            ack_packet, _ = sock.recvfrom(1024)
        except socket.timeout:
            print("RDT_send: timeout, resending window")
            for i in range(base, next_seq):
                seq = i % SEQ_MOD
                packet = build_packet(FLAG_DATA, seq, chunks[i])
                print(f"RDT_send: resending seq={seq} data={chunks[i]}")
                UDT_send(sock, addr, packet, channel)
            continue

        if is_corrupt(ack_packet):
            print("RDT_send: corrupt ACK ignored")
            continue

        _, ack_seq, flag, _ = parse_packet(ack_packet)
        if flag != FLAG_ACK:
            continue

        ack_index = None
        for i in range(base, next_seq):
            if i % SEQ_MOD == ack_seq:
                ack_index = i
        if ack_index is not None:
            base = ack_index + 1
            print(f"RDT_send: ACK received for seq={ack_seq}, base -> {base}")


def RDT_recv(
    sock: socket.socket,
    packet: bytes,
    addr: Tuple[str, int],
    expected_seq: int,
    channel: UnreliableChannel,
) -> Tuple[Optional[bytes], int]:
    if is_corrupt(packet):
        print("RDT_recv: corrupted packet ignored")
        return None, expected_seq

    data, seq, flag, _ = parse_packet(packet)
    if flag != FLAG_DATA:
        return None, expected_seq

    if seq != expected_seq:
        print(f"RDT_recv: out-of-order seq={seq}, expected={expected_seq}")
        return None, expected_seq

    print(f"RDT_recv: received seq={seq} data={data}")
    ack_packet = build_packet(FLAG_ACK, seq, b"\x00" * DATA_SIZE)
    UDT_send(sock, addr, ack_packet, channel)

    return data, (expected_seq + 1) % SEQ_MOD


def generate_random_data(total_bytes: int = 40) -> bytes:
    letters = [random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(total_bytes)]
    return "".join(letters).encode("ascii")

