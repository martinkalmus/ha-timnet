"""Modbus TCP minimal client for Home Assistant integration."""
import socket
import struct
from typing import List


class MinimalModbusTcpClient:
    """Minimal Modbus TCP client (handles non-standard MBAP headers)."""

    def __init__(self, host: str, port: int = 502, timeout: float = 3.0, unit: int = 1):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.unit = unit
        self._tid = 0

    def _next_tid(self) -> int:
        self._tid = (self._tid + 1) & 0xFFFF
        return self._tid

    def _send_request(self, pdu: bytes) -> bytes:
        tid = self._next_tid()
        protocol = 0
        length = len(pdu) + 1
        header = struct.pack(">HHHB", tid, protocol, length, self.unit)
        adu = header + pdu
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as s:
            s.settimeout(self.timeout)
            s.sendall(adu)
            data = s.recv(4096)
            if len(data) < 7:
                raise IOError("Incomplete response")
            pdu_resp = data[7:]
            return pdu_resp

    def read_holding_registers(self, address: int, count: int = 1) -> List[int]:
        """Read holding registers."""
        if count < 1 or count > 125:
            raise ValueError("count must be 1..125")
        pdu = struct.pack(">BHH", 3, address & 0xFFFF, count & 0xFFFF)
        resp = self._send_request(pdu)
        if not resp:
            raise IOError("No response")
        fc = resp[0]
        if fc & 0x80:
            raise IOError(f"Exception response: {resp.hex()}")
        byte_count = resp[1]
        regs_bytes = resp[2:2+byte_count]
        regs = []
        for i in range(0, len(regs_bytes), 2):
            if i+1 < len(regs_bytes):
                # Read as big-endian (standard Modbus)
                regs.append(struct.unpack('>H', regs_bytes[i:i+2])[0])
        return regs[:count]
