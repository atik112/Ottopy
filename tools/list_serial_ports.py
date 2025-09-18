# List available serial ports and attempt a simple PING at 9600 & 115200
import time
from robot_system.arduino.arduino_controller import available_ports, ArduinoController

def try_handshake(baud):
    try:
        ctl = ArduinoController(baud=baud)
        ctl.send_data("PING")
        time.sleep(0.2)
        print(f"[{baud}] denendi, port:", ctl.port)
        for _ in range(10):
            line = ctl.read_line()
            if line:
                print(f"[{baud}] yanıt:", line.strip())
                break
            time.sleep(0.1)
        ctl.close()
    except Exception as e:
        print(f"[{baud}] başarısız:", e)

def main():
    print("Mevcut portlar:", available_ports())
    print("9600/115200 PING testleri:")
    for b in (9600, 115200):
        try_handshake(b)

if __name__ == "__main__":
    main()
