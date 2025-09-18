from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO
import hashlib
import os

is_speaking = False
CACHE_DIR = "voice_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def speak(text, emotion="nötr"):
    global is_speaking
    is_speaking = True

    print(f"Otto ({emotion}):", text)

    try:
        # Duyguya göre farklı ses özellikleri ayarla
        slow = False
        speed = 1.25  # varsayılan

        if emotion in ["üzgün", "kırgın", "yorgun"]:
            slow = True
            speed = 1.0
            text = "... " + text
        elif emotion in ["mutlu", "heyecanlı"]:
            speed = 1.3
        elif emotion in ["sinirli", "öfke"]:
            text = text.upper() + "!"
            speed = 1.1

        # Caching: Aynı ses daha önce üretildiyse kayıttan çal
        hash_name = hashlib.md5((text + emotion).encode("utf-8")).hexdigest()
        cache_path = os.path.join(CACHE_DIR, f"{hash_name}.mp3")

        if os.path.exists(cache_path):
            sound = AudioSegment.from_file(cache_path, format="mp3")
        else:
            tts = gTTS(text=text, lang='tr', slow=slow)
            tts.save(cache_path)
            sound = AudioSegment.from_file(cache_path, format="mp3")

        sound = sound.speedup(playback_speed=speed)
        play(sound)

    except Exception as e:
        print("Ses oluşturulamadı:", e)

    is_speaking = False