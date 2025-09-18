import time

try:
    import serial
    ARDUINO_AVAILABLE = True
except ImportError:
    ARDUINO_AVAILABLE = False

class MotorController:
    def __init__(self, port="/dev/ttyACM0", baudrate=9600):
        self.arduino = None
        if ARDUINO_AVAILABLE:
            try:
                self.arduino = serial.Serial(port, baudrate, timeout=1)
                time.sleep(2)
                print("Arduino'ya bağlandı.")
            except Exception as e:
                print(f"Arduino bağlantısı başarısız: {e}")
        else:
            print("PySerial kütüphanesi bulunamadı, Arduino bağlantısı yapılmayacak.")

    def send_command(self, command):
        if self.arduino and self.arduino.is_open:
            try:
                self.arduino.write(command.encode())
                print(f"Komut gönderildi: {command}")
            except Exception as e:
                print(f"Komut gönderilemedi: {e}")
        else:
            print(f"Arduino bağlı değil, '{command}' komutu gönderilemedi.")

    def close(self):
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
            print("Arduino bağlantısı kapatıldı.")
