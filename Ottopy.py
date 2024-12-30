import os
import time
import glob
import random
import serial
import speech_recognition as sr
import pygame
import serial.tools.list_ports
import playsound3
import traceback
from gtts import gTTS
import openai
import json
import threading
import schedule

user_data = {}

# OpenAI API anahtarını çevresel değişkenden al
openai.api_key = os.getenv("OPENAI_API_KEY")  # Çevresel değişkeni kullanarak API anahtarını alın

# Arduino'nun bağlı olduğu seri portu belirtin
def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Eğer port, 'Arduino' veya 'USB' kelimelerini içeriyorsa, muhtemelen Arduino bağlıdır
        if 'Arduino' in port.description or 'USB' in port.description:
            return port.device
    return None  # Arduino bulunmazsa None döner

# Arduino'nun bağlı olduğu seri portu bul
arduino_port = find_arduino_port()
print(arduino_port)

if arduino_port is None:
    print("Arduino bağlı seri port bulunamadı.")
    exit(1)

baud_rate = 9600  # Arduino'nun seri iletişim hızı

try:
# Seri portu aç
    ser = serial.Serial(arduino_port, baud_rate)
    print(f"{arduino_port} seri portu açıldı.")
    time.sleep(2)
    if not ser.is_open:
        print("Seri port açılamadı.")
        exit(1) # Programı sonlandır
except serial.SerialException as e:
    print(f"Seriport hatası :{e}")
    exit(1)
fart=random.randint(400, 1000)
fart_reset=0

# Arduino ile bağlantı kurana kadar bekleyin
time.sleep(2)

facesound = glob.glob("face/*.wav")
opensound = glob.glob("open/*.wav")
boredsound = glob.glob("bored/*.wav")
fallsound = glob.glob("fall/*.wav")

def daily_task():
    print("Günlük görevler başladı.")
    konus("Uyku saati geldi. İyi geceler.")
    
schedule.every().day.at("21:00").do(daily_task)

def update_user_data(user_id, command, response):
    if not os.path.exists("use_data.json"):
        with open ("user_data.json","w") as f:
            json.dump({},f, indent =4)

    try:
        if user_id not in user_data:
            user_data[user_id] = {"commands": [], "responses": []}
        
        user_data[user_id]["commands"].append(command)
        user_data[user_id]["responses"].append(response)
        
        with open('user_data.json', 'w') as f:
            json.dump(user_data, f, indent=4)  # Veriyi daha okunabilir şekilde kaydet
    except Exception as e:
        print(f"User data güncellenemedi: {e}")

def get_user_preferences(user_id):
    # Kullanıcı tercihlerinden öğrenme
    if user_id in user_data:
        return user_data[user_id]
    else:
        print(f"User{user_id} preferences not found.")
    return {}

def listen_for_commands():
    """Mikrofonla sesli komutları alır."""
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("Sesli komut almak için konuşun...")
        recognizer.adjust_for_ambient_noise(source)  # Ortam gürültüsüne uyum sağla
        try:
            audio = recognizer.listen(source, timeout=5)  # Timeout ekledim
        except sr.WaitTimeoutError:
            print("Zaman aşımına uğradı, lütfen tekrar deneyin.")
            return None
        except sr.RequestError as e:
            print(f"Google API hatası: {e}")
            return None

    try:
        command = recognizer.recognize_google(audio, language="tr-TR")  # Google API kullanarak ses metne dönüştür
        print(f"Alınan komut: {command}")
        return command.lower()
    except sr.UnknownValueError:
        print("Anlaşılamayan bir ses. Lütfen tekrar deneyin.")
        return None
    except sr.RequestError as e:
        print(f"Google API hatası: {e}")
        return None

def konus(metin):
    try:
        tts = gTTS(text=metin, lang='tr')  # Türkçe seslendirme
        tts.save("konusma.mp3")  # Dosyayı kaydet
        playsound3.playsound("konusma.mp3", True)  # Ses dosyasını çal. Bloklayıcıdır (True), yani ses bitene kadar kod devam etmez.
        os.remove("konusma.mp3")  # Dosyayı sil
    except Exception as e:
        print(f"gTTS hatası: {e}")
        traceback.print_exc()

def opening_sound():
    """Açılışta bir ses dosyası çalar."""
    filenameOpen = random.choice(opensound)  # 'open' klasöründen rastgele bir ses seç
    print(f"Çalan ses: {filenameOpen}")
    try:
        pygame.mixer.init()  # pygame ses modülünü başlat
        pygame.mixer.music.load(filenameOpen)  # Ses dosyasını yükle
        pygame.mixer.music.play()  # Sesi çalmaya başla
    except pygame.error as e:
        print(f"Ses hatası: {e}")
    while pygame.mixer.music.get_busy():  # Ses bitene kadar bekle
        time.sleep(0.1)  # Kısa bir süre bekleyerek CPU'nun boşta kalmasını sağla
        
def play_sound():
    """Açılışta bir ses dosyası çalmayı başlat."""
    opening_sound()

def tell_joke():
    jokes=[
        "Bir robot neden soğuk bir kahve içer? Çünkü sıcak içecekleri sevmiyor!",
        "Robotlar neden bazen yavaş cevap verir? Çünkü biraz donmuşlar!",
        "Hangi hayvan bilgisayar kullanamaz? Kediler, çünkü hep 'fareyi' kaybederler!",
        "Saat neden her zaman yavaş çalışır? Çünkü zamanla yarışıyordur!"
    ]
    
    joke =random.choice(jokes)
    konus(joke)

def send_command(command):
    """Verilen komutu Arduino'ya gönderir."""
    ser.write((command + '\n').encode())  # Komut gönder
    print(f"PC: {command} komutu gönderildi.")

def receive_data():
    """Arduino'dan gelen veriyi alır."""
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').strip()
        print(f"Arduino: {data}")

def get_ai_response(user_input):
    """OpenAI Chat API ile yapay zeka yanıtı alır."""
    try:
        # OpenAI API'ye bir istek gönder
        response = openai.chat.completions.create(
            model="gpt-4",  # veya gpt-4, kullanmak istediğiniz model
            messages=[
                {"role": "system", "content": "Sen, bir konuşma asistanısın."},
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

def get_sentiment(user_input):
    """OpenAI API ile metnin duygusal analizini yapar."""
    try:
        # OpenAI API'ye bir istek gönder
        response = openai.chat.completions.create(
            model="gpt-4",  # Modeli belirleyin (gpt-4, gpt-3.5-turbo, vb.)
            messages=[
                {"role": "system", "content": "Sen, bir duygu analiz asistanısın."},
                {"role": "user", "content": f"Şu metnin duygusunu analiz et: '{user_input}'"},
            ],
            max_tokens=100  # Yanıt uzunluğunu sınırlayın
        )

        # Yanıtı al ve duyguyu çıkart
        ai_mood = response.choices[0].message.content
        
        # Duygu analizi için genişletilmiş kategoriler
        if "mutluluk" in ai_mood:
            return "Mutluluk"
        elif "üzüntü" in ai_mood:
            return "Üzüntü"
        elif "öfke" in ai_mood:
            return "Öfke"
        elif "korku" in ai_mood:
            return "Korku"
        elif "şaşkınlık" in ai_mood:
            return "Şaşkınlık"
        elif "huzur" in ai_mood:
            return "Huzur"
        elif "heyecan" in ai_mood:
            return "Heyecan"
        elif "sinir" in ai_mood or "sinirli" in ai_mood:
            return "Sinirli"
        elif "endişe" in ai_mood:
            return "Endişe"
        elif "hayal kırıklığı" in ai_mood:
            return "Hayal Kırıklığı"
        elif "nötr" in ai_mood:
            return "Nötr"
        else:
            # Duygu daha karmaşık olduğunda detaylı analiz yapabiliriz
            if "olumlu" in ai_mood:
                return "Olumlu"
            elif "olumsuz" in ai_mood:
                return "Olumsuz"
            return "Belirli bir duygu tespiti yapılamadı."
        
    except Exception as e:
        print(f"Yapay zeka hatası: {e}")
        return "Üzgünüm, şu an duygu analizini yapamıyorum."

def handle_command(command):
    """Komutu analiz et ve gerekirse Arduino'ya komut gönder."""
    user_id="Meva"
    user_prefereces=get_user_preferences(user_id)
    
    if command == "Dans et":
        send_command("dance")
    elif command == "zıpla":
        send_command("jump")
        ai_response ="Elimden bu kadar geliyor"
        konus(ai_response)
    elif command == "selam":
        send_command("bend")
        ai_response = "Merhaba, ben Otto. Size nasıl yardımcı olabilirim?"
        konus(ai_response)
    elif command == "nasılsın":
        send_command("bend")
        ai_response = "Ben bir robotum, benim için her şey yolunda. Peki ya sen?"
        konus(ai_response)
    elif command == "kendine iyi bak":
        send_command("shaka_leg")
        ai_response = "Teşekkür ederim, sen de kendine iyi bak."
        konus(ai_response)
    elif command in ["gez", "gezin", "yürü", "yürüyüş yap", "dolan", "gez gel" ]:
        send_command("wander")
    elif command in ["kaç", "geri git", "kaçın", "kaç benden"]:
        send_command("get_back")
    elif command in ["pırtlat", "pırt yap"]:
        send_command("fart")
    elif command == "sihir yap":
        send_command("magic")
    elif command == "şaka yap":
        tell_joke()
        send_command("bend")
    elif command == "kapat":
        ai_response = "Kapanmamı istiyor musun?"
        print(ai_response)
        konus(ai_response)
        start_time = time.time()
        while time.time() - start_time < 10:  # 5 saniye içinde yeni bir komut al
            command = listen_for_commands()
            if command in["evet", "tamam", "olur", "kapat", "kapan", "kapanabilirsin"]:
                ai_response = "Tamam, kapanıyorum."
                print(ai_response)
                konus(ai_response)
                if ser.is_open:
                    ser.close()  # Seri portu kapat
                    print("Seri port kapatıldı.")
                return True  # Programı sonlandırmak için True döndür
            elif command:
                ai_response = "Anladım, devam ediyorum."
                print(ai_response)
                konus(ai_response)
                return False
    else:
        ai_response = get_ai_response(command)
        print(ai_response)
        konus(ai_response)
        sentiment = get_sentiment(ai_response)
        print(sentiment)

        if sentiment == "Olumlu":
            send_command("OttoHappy")
        elif sentiment == "Olumsuz":
            send_command("OttoSad")
        elif sentiment == "Mutluluk":
            send_command("OttoSuperHappy")
        elif sentiment == "Üzüntü":
            send_command("OttoSad")
        elif sentiment == "Endişe":
            send_command("Fretful")
        elif sentiment =="Hayal Kırıklığı":
            send_command("OttoSad")
        elif sentiment =="Heyecan":
            send_command("OttoSuperHappy")
        elif sentiment == "Korku":
            send_command("Frightened")
        elif sentiment == "Öfke":
            send_command("Angry")
        elif sentiment == "Sinirli":
            send_command("Angry")
        elif sentiment == "Şaşkınlık":
            send_command("Surprised")
        elif sentiment =="Huzur":
            send_command("Love")
        elif sentiment == "Nötr":
            print("Nötr")
            # Nötr durumda herhangi bir işlem yapılmaz veya başka bir komut gönderilebilir
    update_user_data(user_id, command, ai_response)
        
    return False

def main_loop():
    global fart_reset
    fart_reset+=random.randint(1,5)
    if fart_reset >= fart:
        send_command("fart")
        fart_reset=0
    
    """Ana döngü, komut al ve işleyerek sistemdeki diğer işlemleri kontrol et."""
    play_sound()  # Açılışta bir ses çal
    while True:
        schedule.run_pending()
        time.sleep(1)
        command = listen_for_commands()
        if command:
            exit_flag = handle_command(command)
            if exit_flag:
                break

try:
    # Yeni bir thread başlatarak ana döngüyü çalıştır
    main_thread = threading.Thread(target=main_loop)
    main_thread.start()
except KeyboardInterrupt:
    print("Program sonlandırıldı.")
