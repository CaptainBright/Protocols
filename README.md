# Go-Back-N Reliable Data Transfer (N=3)

This repository contains a minimal Go-Back-N reliable data transfer (RDT) implementation over UDP.
The implementation provides the four required functions:

- `RDT_send()` and `RDT_recv()` for reliable, ordered transfer with a sliding window.
- `UDT_send()` and `UDT_recv()` to simulate an unreliable transport.

## Packet Format

| Field | Size |
| --- | --- |
| Data | 4 bytes |
| Sequence Number | 1 byte |
| Flag | 1 byte |
| Checksum | 2 bytes |

## Running the Demo

1. Start the server:

   ```bash
   python src/server.py
   ```

2. In another terminal, start the client:

   ```bash
   python src/client.py
   ```

The client generates 40 bytes (10 packets) of random alphabetic data and sends them to the server.

## Q1 Answer

In Go-Back-N with `N=3`, if every 5th packet is lost while sending 10 packets, the total number of
transmissions is **14** (10 original + 3 retransmissions after packet 5 is lost + 1 retransmission
for packet 10). See `src/simulate_q1.py` for the deterministic simulation that prints the log and
transmission count.
