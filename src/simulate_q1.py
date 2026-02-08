from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass
class SimulationResult:
    transmissions: int
    log: List[str]


def simulate_gbn_every_fifth_loss(total_packets: int, window_size: int) -> SimulationResult:
    loss_every = 5
    lost_packets: Set[int] = {pkt for pkt in range(1, total_packets + 1) if pkt % loss_every == 0}
    base = 1
    next_seq = 1
    expected = 1
    transmissions = 0
    log: List[str] = []
    send_count: Dict[int, int] = {}

    while base <= total_packets:
        progressed = False
        while next_seq <= total_packets and next_seq < base + window_size:
            transmissions += 1
            send_count[next_seq] = send_count.get(next_seq, 0) + 1
            is_lost = send_count[next_seq] == 1 and next_seq in lost_packets
            status = "LOST" if is_lost else "OK"
            log.append(f"send {next_seq} ({status})")

            if not is_lost:
                if next_seq == expected:
                    log.append(f"ack {next_seq}")
                    expected += 1
                    base = expected
                    progressed = True
                else:
                    log.append(f"discard {next_seq} (expected {expected})")

            next_seq += 1

        if not progressed and base < next_seq:
            log.append(f"timeout on {base}, retransmit {list(range(base, next_seq))}")
            for pkt in range(base, next_seq):
                transmissions += 1
                send_count[pkt] = send_count.get(pkt, 0) + 1
                is_lost = send_count[pkt] == 1 and pkt in lost_packets
                status = "LOST" if is_lost else "OK"
                log.append(f"resend {pkt} ({status})")
                if not is_lost and pkt == expected:
                    log.append(f"ack {pkt}")
                    expected += 1
                    base = expected

    return SimulationResult(transmissions=transmissions, log=log)


def main() -> None:
    result = simulate_gbn_every_fifth_loss(total_packets=10, window_size=3)
    print("Go-Back-N (N=3) with every 5th packet lost")
    for entry in result.log:
        print(entry)
    print(f"Total transmissions: {result.transmissions}")


if __name__ == "__main__":
    main()
