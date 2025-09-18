
import random
import serial
import serial.tools.list_ports

def send_random_command():
    secenekler = ["turn_right", "turn_left", "walk_forward", "walk_backward"]
    komut = random.choice(secenekler)

    # Portları kontrol et
    portlar = [port.device for port in serial.tools.list_ports.comports()]
    olası_portlar = portlar + ["/dev/ttyUSB0", "/dev/ttyACM0", "COM3", "COM4"]

    for port in olası_portlar:
        try:
            ser = serial.Serial(port, 9600, timeout=2)
            ser.write((komut + '\n').encode())
            print(f"[Helpers] Rasgele komut gönderildi: {komut}")
            ser.close()
            return
        except Exception as e:
            continue

    print("[Helpers] Hiçbir porta bağlanılamadı.")
