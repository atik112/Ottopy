import random
from ai.user_preferences import get_user_preferences
import threading
import serial
import serial.tools.list_ports
import time
from voice.text_to_speech import konus
from voice.speech_recognition import listen_once
from ai.openai_response import get_ai_response, get_sentiment

class CommandProcessor:
    def __init__(self, ai_module, arduino_module):
        self.ai = ai_module
        self.arduino = arduino_module
        self.ser = None
        self.walk = True
        self.listening = True

    def connect_to_arduino(self):
        # Kullanılabilecek portları otomatik bul
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        
        # Manuel port listesi (Linux ve Windows için)
        arduino_ports = available_ports + ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2", "/dev/ttyACM0", "COM3", "COM4"]

        for port in arduino_ports:
            try:
                self.ser = serial.Serial(port, 9600, timeout=2)  # Timeout eklendi
                print(f"Bağlantı kuruldu: {port}")
                return True
            except serial.SerialException as e:
                print(f"{port} portuna bağlanılamadı. Hata: {e}")
        
        print("Arduino bağlantısı kurulamadı!")
        return False

    def reconnect_serial(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        return self.connect_to_arduino()

    def send_command_async(self, command):
        def send_command_thread():
            try:
                if self.ser and self.ser.is_open:
                    self.ser.write((command + '\n').encode())
                    print(f"PC: {command} komutu gönderildi.")
                else:
                    print("Seri port bağlantısı kapalı. Yeniden bağlanılıyor...")
                    if self.reconnect_serial():
                        self.ser.write((command + '\n').encode())
                        print(f"PC: {command} komutu gönderildi.")
            except Exception as e:
                print(f"Seri port hatası: {e}")
                if "Input/output error" in str(e):
                    print("Bağlantı kesildi. Yeniden bağlanılıyor...")
                    if self.reconnect_serial():
                        self.ser.write((command + '\n').encode())
                        print(f"PC: {command} komutu gönderildi.")

        threading.Thread(target=send_command_thread).start()

    def handle_command(self, command):
        user_id = "Meva"
        user_preferences = get_user_preferences(user_id)
        ai_response = ""
        command_to_send = None

        if command == "Dans et":
            dancecommand = ["moonwalker", "dance"]
            command_to_send = random.choice(dancecommand)
            ai_response = "İşte dans ediyorum!"
        elif command == "zıpla":
            command_to_send = "jump"
            ai_response = "Elimden bu kadar geliyor."
        elif command == "selam":
            command_to_send = "bend"
            ai_response = "Merhaba, ben Otto. Size nasıl yardımcı olabilirim?"
        elif command == "nasılsın":
            command_to_send = "bend"
            ai_response = "Ben bir robotum, benim için her şey yolunda. Peki ya sen?"
        elif command == "kendine iyi bak":
            command_to_send = "shaka_leg"
            ai_response = "Teşekkür ederim, sen de kendine iyi bak."
        elif command == "gez":
            for _ in range(3):
                self.send_command_async("walk_forward")
            command_to_send = random.choice(["turn_right", "turn_left"])
            ai_response = "Biraz dolaşıyorum!"
        elif command in ["kaç", "geri git"]:
            for _ in range(3):
                self.send_command_async("walk_backward")
            command_to_send = random.choice(["turn_right", "turn_left"])
            ai_response = "Tamam, geri çekiliyorum!"
        elif command in ["Pırtlat", "pırt yap"]:
            command_to_send = "fart"
            ai_response = "Umarım kimse duymamıştır!"
        elif command in ["dur", "tamam dur", "gezme", "yerinde dur"]:
            ai_response = "Tamam duruyorum"
            self.walk = False
            command_to_send = None
        elif command == "sihir yap":
            command_to_send = "magic"
            ai_response = "Abrakadabra!"
        elif command == "kapat":
            ai_response = "Kapanmamı istiyor musun?"
            konus(ai_response)
            start_time = time.time()
            while time.time() - start_time < 10:
                command = listen_once()
                if command in ["evet", "tamam", "olur", "kapat", "kapan", "kapanabilirsin"]:
                    ai_response = "Tamam, kapanıyorum."
                    konus(ai_response)
                    if self.ser:
                        self.ser.close()
                    return True
                elif command:
                    ai_response = "Anladım, devam ediyorum."
                    konus(ai_response)
                    return False
        else:
            ai_response = get_ai_response(command)
            sentiment = get_sentiment(ai_response)
            emotion_mapping = {
                "Mutluluk": "OttoSuperHappy",
                "Üzüntü": "OttoSad",
                "Öfke": "Angry",
                "Heyecan": "OttoSuperHappy",
                "Korku": "Frightened",
                "Huzur": "Love"
            }
            command_to_send = emotion_mapping.get(sentiment, None)

        if command_to_send:
            self.send_command_async(command_to_send)
        konus(ai_response)

    def send_random_command():
        """Anlaşılamayan komutlar için rastgele hareket komutu gönderir."""
        secenek = ["turn_right", "turn_left", "walk_forward", "walk_backward"]
        secim = random.choice(secenek)
        send_command_async(secim)  # Rastgele bir komut gönder