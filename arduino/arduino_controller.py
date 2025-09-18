import time
import logging
from typing import Optional, List, Tuple

try:
    import serial
    import serial.tools.list_ports as list_ports
except Exception as e:
    serial = None
    list_ports = None
    logging.getLogger(__name__).exception("PySerial import failed: %s", e)

DEFAULT_BAUD = 9600
DEFAULT_TIMEOUT = 1.0

def available_ports() -> List[Tuple[str, str]]:
    if not list_ports:
        return []
    return [(p.device, p.description) for p in list_ports.comports()]

def autodetect_port(preferred: Optional[str] = None) -> Optional[str]:
    if preferred:
        return preferred
    ports = available_ports()
    scores = []
    for dev, desc in ports:
        sdesc = (desc or "").lower()
        score = 0
        if "arduino" in sdesc: score += 5
        if "usb2.0-ser" in sdesc: score += 4
        if "ch340" in sdesc: score += 3
        if "cp210" in sdesc: score += 3
        if "/ttyacm" in dev.lower(): score += 2
        if "/ttyusb" in dev.lower(): score += 2
        scores.append((score, dev))
    if not scores:
        return None
    scores.sort(reverse=True)
    return scores[0][1]

class ArduinoController:
    def __init__(self, port: Optional[str] = None, baud: int = DEFAULT_BAUD, timeout: float = DEFAULT_TIMEOUT,
                 dtr_reset: bool = True, do_handshake: bool = True):
        self.log = logging.getLogger(self.__class__.__name__)
        if serial is None:
            raise RuntimeError("pyserial yüklü değil. `pip install pyserial` gerekir.")
        self.port = autodetect_port(port)
        if not self.port:
            raise RuntimeError(f"Arduino portu bulunamadı. Mevcut portlar: {available_ports()}")
        self.baud = baud or DEFAULT_BAUD
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
        if dtr_reset:
            try:
                self.ser.setDTR(False); time.sleep(0.05); self.ser.setDTR(True)
            except Exception:
                pass
        time.sleep(2.0)
        self.flush()
        self.log.info("[Arduino] Bağlantı kuruldu: %s @ %d", self.port, self.baud)
        if do_handshake:
            self._handshake()

    def _handshake(self) -> None:
        try:
            self.write_line("PING")
            t0 = time.time()
            while time.time() - t0 < 3.0:
                line = self.read_line()
                if not line:
                    continue
                up = line.strip().upper()
                if up in ("OK", "READY", "PONG", "ACK:PING"):
                    self.log.info("[Arduino] Handshake OK: %s", up)
                    return
            self.log.warning("[Arduino] Handshake yanıtı alınamadı.")
        except Exception as e:
            self.log.warning("[Arduino] Handshake hata: %s", e)

    def flush(self) -> None:
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
        except Exception:
            pass

    def write_line(self, text: str) -> None:
        if not text.endswith("\n"):
            text += "\n"
        data = text.encode("utf-8", "ignore")
        self.ser.write(data)
        self.ser.flush()
        self.log.debug("[Arduino]<= %r", text.strip())

    def read_line(self) -> str:
        try:
            line = self.ser.readline().decode("utf-8", "ignore")
            if line:
                self.log.debug("[Arduino]=> %r", line.strip())
            return line
        except Exception:
            return ""

    def send_data(self, text: str) -> None:
        self.write_line(text)

    def close(self) -> None:
        try:
            self.ser.close()
        except Exception:
            pass
