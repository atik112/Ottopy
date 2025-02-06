import os
import time
import random
import serial
import speech_recognition as sr
import playsound3
import traceback
from pydub import AudioSegment
from pydub.playback import play
from gtts import gTTS
import openai
import io
import json
import threading
import sounddevice  # to hide ALSA errors
import schedule
import serial.tools.list_ports

stop_listening=False
listening = True

try:
    with open('user_data.json', 'r') as f:
        user_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    user_data = {}

walk = True
# OpenAI API anahtarını çevresel değişkenden al
openai.api_key = "OPENAI_API_KEY"  # Çevresel değişkeni kullanarak API anahtarını alın

listening = True  # Ses dinleme durumu
ser = None  # Eğer bağlantı başarısız olursa None olarak kalmalı

def connect_to_arduino():
    global ser

    
    # Kullanılabilecek portları otomatik bul
    available_ports = [port.device for port in serial.tools.list_ports.comports()]
    
    # Manuel port listesi (Linux ve Windows için)
    arduino_ports = available_ports + ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2", "/dev/ttyACM0", "COM3", "COM4"]

    for port in arduino_ports:
        try:
            ser = serial.Serial(port, 9600, timeout=2)  # Timeout eklendi
            print(f"Bağlantı kuruldu: {port}")
            return True
        except serial.SerialException as e:
            print(f"{port} portuna bağlanılamadı. Hata: {e}")
    
    print("Arduino bağlantısı kurulamadı!")
    return False  # Hiçbir porta bağlanılamadıysa False döndür

def reconnect_serial():
    global ser
    if ser and ser.is_open:
        ser.close()
    return connect_to_arduino()


fart = random.randint(400, 1000)
fart_reset = 0

# Arduino ile bağlantı kurana kadar bekleyin
time.sleep(2)


def daily_task():
    print("Günlük görevler başladı.")
    konus("Uyku saati geldi. İyi geceler.")


schedule.every().day.at("21:00").do(daily_task)


def update_user_data(user_id, command, response):
    if user_id not in user_data:
        user_data[user_id] = {"commands": [], "responses": []}

    user_data[user_id]["commands"].append(command)
    user_data[user_id]["responses"].append(response)

    # Veriyi dosyaya kaydet
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)


def get_user_preferences(user_id):
    # Kullanıcı tercihlerinden öğrenme
    if user_id in user_data:
        return user_data[user_id]
    return None

def listen_once():
    """Tek seferlik dinleme fonksiyonu, konuşma kesintisiz devam eder."""
    global listening, stop_listening
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("Dinleme başlıyor...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

    while not stop_listening:
        if not listening: 
            continue # Bot konuşuyorsa bekle

        with mic as source:
            try:
                print("Dinliyorum...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                command = recognizer.recognize_google(audio, language="tr-TR")
                print(f"Kullanıcı: {command}")

                return command.lower()
            except sr.UnknownValueError:
                print("Anlaşılamadı, tekrar dene.")
                continue
            except sr.RequestError as e:
                print(f"Bağlantı hatası: {e}")
                send_random_command()
                continue
            except sr.WaitTimeoutError:
                print("Zaman aşımı, dinlemeye devam ediyorum...")
                send_random_command()
                continue

    return None

def send_random_command():
    """Anlaşılamayan komutlar için rastgele hareket komutu gönderir."""
    secenek = ["turn_right", "turn_left", "walk_forward", "walk_backward"]
    secim = random.choice(secenek)
    send_command_async(secim)  # Rastgele bir komut gönder

def konus(metin, hiz=1.3):
    global listening
    listening = False  # Konuşma sırasında dinlemeyi durdur

    try:
        tts = gTTS(text=metin, lang='tr')
        ses_dosyasi = io.BytesIO()
        tts.write_to_fp(ses_dosyasi)
        ses_dosyasi.seek(0)

        ses = AudioSegment.from_file(ses_dosyasi, format="mp3")
        hizli_ses = ses.speedup(playback_speed=hiz)
        play(hizli_ses)
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        listening = True  # Konuşma bittiğinde dinlemeyi tekrar aç

def send_command_async(command):
    # Seri porta komut göndermeyi ayrı bir thread'de çalıştırır.
    def send_command_thread():
        global ser
        try:
            if ser and ser.is_open:
                ser.write((command + '\n').encode())  # Komutu gönder
                print(f"PC: {command} komutu gönderildi.")
            else:
                print("Seri port bağlantısı kapalı. Yeniden bağlanılıyor...")
                if reconnect_serial():
                    ser.write((command + '\n').encode())  # Komutu gönder
                    print(f"PC: {command} komutu gönderildi.")
        except Exception as e:
            print(f"Seri port hatası: {e}")
            if "Input/output error" in str(e):
                print("Bağlantı kesildi. Yeniden bağlanılıyor...")
                if reconnect_serial():
                    ser.write((command + '\n').encode())  # Komutu gönder
                    print(f"PC: {command} komutu gönderildi.")

    # Ayrı bir thread başlat
    threading.Thread(target=send_command_thread).start()


def receive_data():
    """Arduino'dan gelen veriyi alır."""
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').strip()
        print(f"Arduino: {data}")


def get_ai_response(user_input):
    #OpenAI Chat API ile yapay zeka yanıtı alır.
    try:
        # OpenAI API'ye bir istek gönder
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # veya gpt-4, kullanmak istediğiniz model
            messages=[
                {"role": "system", "content": "Sen çok arkadaşça ve samimi bir dil kullanarak cevap veriyorsun."},
                {"role": "user", "content": user_input},
            ],
            max_tokens=100  # Yapay zekanın maksimum kelime sayısı
        )

        # Yanıtı al ve döndür
        ai_response = response.choices[0].message.content
        return ai_response
    except Exception as e:
        print(f"Yapay zeka hatası: {e}")
        return "Üzgünüm, şu an cevap veremiyorum."

def handle_command(command):
    #Komutu analiz et ve gerekirse Arduino'ya komut gönder.
    global listening  # Dinleme durumunu yönetmek için global değişken

    user_id = "Meva"
    user_preferences = get_user_preferences(user_id)
    ai_response = ""
    command_to_send = None  # Initialize the variable
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
            send_command_async("walk_forward")
        command_to_send = random.choice(["turn_right", "turn_left"])
        ai_response = "Biraz dolaşıyorum!"
    elif command in ["kaç", "geri git"]:
        for _ in range(3):
            send_command_async("walk_backward")
        command_to_send = random.choice(["turn_right", "turn_left"])
        ai_response = "Tamam, geri çekiliyorum!"
    elif command in ["Pırtlat", "pırt yap"]:
        command_to_send = "fart"
        ai_response = "Umarım kimse duymamıştır!"
    elif command in ["dur", "tamam dur", "gezme", "yerinde dur"]:
        ai_response = "Tamam duruyorum"
        global walk
        walk = False
        command_to_send = None
    elif command == "sihir yap":
        command_to_send = "magic"
        ai_response = "Abrakadabra!"
    elif command == "kapat":
        ai_response = "Kapanmamı istiyor musun?"
        konus(ai_response)
        start_time = time.time()
        while time.time() - start_time < 10:
            command = listen_continuously()
            if command in ["evet", "tamam", "olur", "kapat", "kapan", "kapanabilirsin"]:
                ai_response = "Tamam, kapanıyorum."
                konus(ai_response)
                ser.close()
                return True
            elif command:
                ai_response = "Anladım, devam ediyorum."
                konus(ai_response)
                return False
    else:
        ai_response = get_ai_response(command)
        sentiment = get_sentiment(ai_response)
        
        # Duygu analizine göre uygun hareketi seç
        emotion_mapping = {
            "Mutluluk": "OttoSuperHappy",
            "Üzüntü": "OttoSad",
            "Öfke": "Angry",
            "Heyecan": "OttoSuperHappy",
            "Korku": "Frightened",
            "Huzur": "Love"
        }
        command_to_send = emotion_mapping.get(sentiment, None)

    def start_conversation():
        print(ai_response)
        konus(ai_response)

    def send_data():
        if command_to_send:
            send_command_async(command_to_send)

    # Konuşmayı başlatan thread
    conversation_thread = threading.Thread(target=start_conversation)
    conversation_thread.start()

    # Seri port komutunu gönderen thread
    send_data_thread = threading.Thread(target=send_data)
    send_data_thread.start()

    # Her iki thread tamamlanana kadar bekleyelim
    conversation_thread.join()
    send_data_thread.join()

    update_user_data(user_id, command, ai_response)

    return False
    
    
def get_sentiment(user_input):
    """OpenAI API ile metnin duygusal analizini yapar."""
    try:
        # OpenAI API'ye bir istek gönder
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Modeli belirleyin (gpt-4, gpt-3.5-turbo, vb.)
            messages=[
                {"role": "system", "content": "Sen, bir duygu analiz asistanısın. Şu metnin duygusunu analiz et ve yalnızca şu kategorilerden birini seç: Mutluluk, Üzüntü, Öfke, Korku, Şaşkınlık, Huzur, Heyecan, Endişe, Hayal Kırıklığı, Nötr, Olumlu, Olumsuz."},
                {"role": "user", "content": f"Şu metnin duygusunu analiz et: '{user_input}'"},
            ],
            max_tokens=100  # Yanıt uzunluğunu sınırlayın
        )

        # Yanıtı al ve duyguyu çıkart
        ai_mood = response.choices[0].message.content
            # Duygular ve ilişkili anahtar kelimeler
        emotion_keywords = {
        "Mutluluk": ["mutluluk", "mutlu", "neşe", "sevinç", "keyif"],
        "Üzüntü": ["üzüntü", "üzgün", "keder", "hüzün", "acı"],
        "Öfke": ["öfke", "sinir", "kızgın", "kızgınlık", "sinirli"],
        "Korku": ["korku", "korkmuş", "endişe", "panik", "dehşet"],
        "Şaşkınlık": ["şaşkınlık", "şaşkın", "şaşırdım", "hayret"],
        "Huzur": ["huzur", "sakin", "rahat", "dingin"],
        "Heyecan": ["heyecan", "heyecanlı", "coşku", "coşkulu"],
        "Endişe": ["endişe", "kaygı", "stres", "tedirgin"],
        "Hayal Kırıklığı": ["hayal kırıklığı", "hayal kırık", "hayalkırıklığı"],
        "Nötr": ["nötr", "normal", "sıradan", "belirsiz"],
        }

        # Duygu skorlarını hesapla
        emotion_scores = {emotion: 0 for emotion in emotion_keywords}

        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in ai_mood.lower():
                    emotion_scores[emotion] += 1

        # En yüksek skora sahip duyguyu bul
        max_emotion = max(emotion_scores, key=emotion_scores.get)
        max_score = emotion_scores[max_emotion]

        # Eğer hiçbir duygu tespit edilemezse
        if max_score == 0:
            if "olumlu" in ai_mood.lower():
                return "Olumlu"
            elif "olumsuz" in ai_mood.lower():
                return "Olumsuz"
            else:
                return "Belirli bir duygu tespiti yapılamadı."

        return max_emotion
        
    except Exception as e:
        print(f"Yapay zeka hatası: {e}")
        return "Üzgünüm, şu an duygu analizini yapamıyorum."

	

def main_loop():
    global fart_reset
    fart_reset += 1
    if fart_reset == fart:
        send_command_async("fart")
        fart_reset = 0

    """Ana döngü, komut al ve işleyerek sistemdeki diğer işlemleri kontrol et."""
    while True:
        schedule.run_pending()
        time.sleep(0.5)
        if listening:
            #command = listen_continuously()
            command = listen_once()
            if command:  # Eğer komut alındıysa
                exit_flag = handle_command(command)
                if exit_flag:
                    break

try:
    # Yeni bir thread başlatarak ana döngüyü çalıştır
    main_thread = threading.Thread(target=main_loop)
    main_thread.start()
except KeyboardInterrupt:
    print("Program sonlandırıldı.")
    ser.close()
