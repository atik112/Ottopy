from http import client
from httpx import get
import serial
import time
import glob
import random
import pyaudio
import speech_recognition as sr
import threading
import pygame
import simpleaudio as sa
import os
from gtts import gTTS
import playsound3
import traceback
import openai

# OpenAI API anahtarını çevresel değişkenden al
openai.api_key = os.getenv("OPENAI_API_KEY")  # Çevresel değişkeni kullanarak API anahtarını alın

# Arduino'nun bağlı olduğu seri portu belirtin
arduino_port = "COM3"  # Windows için COM3, Linux/Mac için "/dev/ttyUSB0" olabilir
baud_rate = 9600  # Arduino'nun seri iletişim hızı

# Seri portu aç
ser = serial.Serial(arduino_port, baud_rate)

# Arduino ile bağlantı kurana kadar bekleyin
time.sleep(2)

facesound = glob.glob("face/*.wav")
opensound = glob.glob("open/*.wav")
boredsound = glob.glob("bored/*.wav")
fallsound = glob.glob("fall/*.wav")

def listen_for_commands():
    """Mikrofonla sesli komutları alır."""
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("Sesli komut almak için konuşun...")
        recognizer.adjust_for_ambient_noise(source)  # Ortam gürültüsüne uyum sağla
        audio = recognizer.listen(source, timeout=5)  # Ses kaydını al

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
        tts = gTTS(text=metin, lang='tr') # Türkçe seslendirme
        tts.save("konusma.mp3") # Dosyayı kaydet
        playsound3.playsound("konusma.mp3", True) # Ses dosyasını çal. Bloklayıcıdır (True), yani ses bitene kadar kod devam etmez.
        os.remove("konusma.mp3") # Dosyayı sil
    except Exception as e:
        print(f"gTTS hatası: {e}")
        traceback.print_exc()

def opening_sound():
    """Açılışta bir ses dosyası çalar."""
    filenameOpen = random.choice(opensound)  # 'open' klasöründen rastgele bir ses seç
    print(f"Çalan ses: {filenameOpen}")
    pygame.mixer.init()  # pygame ses modülünü başlat
    pygame.mixer.music.load(filenameOpen)  # Ses dosyasını yükle
    pygame.mixer.music.play()  # Sesi çalmaya başla
    while pygame.mixer.music.get_busy():  # Ses bitene kadar bekle
        time.sleep(0.1)  # Kısa bir süre bekleyerek CPU'nun boşta kalmasını sağla
        
def play_sound():
    """Açılışta bir ses dosyası çalmayı başlat."""
    opening_sound()
    
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
        return ai_mood
    except Exception as e:
        print(f"Yapay zeka hatası: {e}")
        return "Üzgünüm, şu an duygu analizini yapamıyorum."

try:
    play_sound()  # Açılışta bir ses çal
    while True:
        # Sesli komut al
        command = listen_for_commands()

        if command:
            # Komut geçerli ise, komut Arduino'ya gönder
            if command == "deneme":
                send_command("shake_leg")
                konus("Deneme başladı")
            elif command == "Kapan":
                send_command("STOP")
            elif command == "kapat":
                print("Kapanmamı istiyor musun?")
                konus("Kapanmamı istiyor musun?")
                command = listen_for_commands()
                if command == "evet" or command == "kapan":
                   print("İyi geceler")
                   konus("İyi geceler")
                   break
                else:
                     print("Anladım")
                     konus("Anladım")
                     continue     
            else:
                ai_response = get_ai_response(command)
                print(ai_response)
                konus(ai_response)
                sentiment = get_sentiment(ai_response)
                print(sentiment)
                
                if "olumlu" in sentiment:
                    print("Olumlu")
                    send_command("OttoHappy")
                elif "olumsuz" in sentiment:
                    print("Olumsuz")
                    send_command("OttoSad")
                elif "mutlu" in sentiment:
                    print("Mutlu")
                    send_command("OttoSuperHappy")
                elif "nötr" in sentiment:
                    print("Nötr")
                    # Nötr durumda herhangi bir işlem yapılmaz veya başka bir komut gönderilebilir
           
        # Arduino'dan gelen veriyi al ve ekrana yazdır
        receive_data()

except KeyboardInterrupt:
    print("Program sonlandırıldı.")

finally:
    ser.close()  # Seri portu kapat