import time
from robot_system.arduino.arduino_controller import available_ports, ArduinoController

def try_one(device, baud):
    try:
        ctl = ArduinoController(port=device, baud=baud, do_handshake=True)
        ctl.send_data("PING")
        time.sleep(0.2)
        for _ in range(10):
            line = ctl.read_line()
            if line:
                print(f"[{device} @ {baud}] Yanıt:", line.strip())
                break
            time.sleep(0.1)
        ctl.close()
    except Exception as e:
        print(f"[{device} @ {baud}] Hata: {e}")

def main():
    ports = available_ports()
    print("Mevcut portlar:", ports)
    if not ports:
        print("Hiç port görünmüyor. USB kablo/driver?")
        return
    candidates = sorted(ports, key=lambda p: ("/ttyACM" in p[0], "/ttyUSB" in p[0]), reverse=True)
    for dev, desc in candidates:
        for baud in (9600, 115200):
            try_one(dev, baud)

if __name__ == "__main__":
    main()
