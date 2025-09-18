from voice.speech_recognition import listen_and_recognize
from voice.text_to_speech import speak
from ai.openai_response import get_ai_response, get_sentiment
from sensors.camera import Camera
from sensors.face_emotion import analyze_face_emotion
from arduino.arduino_controller import ArduinoController  # keep it simple
import sounddevice
from ai.user_preferences import (
    get_user_name_by_voice_id,
    register_new_user,
    set_user_mode,
    get_user_mode
)
from ai.mood_manager import get_today_mood
from otto.otto_memory import get_memory_about, add_memory_about
from otto.otto_journal import (
    write_to_journal,
    get_last_entries,
    get_best_memory,
    get_entries_about,
    summarize_today,
    get_important_memories,
    get_last_emotion_for_user,
    needs_goal_review
)
from otto.face_recog import recognize_face, register_new_face
from otto import mood_tracker
from ai.training_rules import add_behavior_rule

from control_system import OttoControlSystem, translate_for_arduino

# Baud/Port config (port may be unsupported by your ArduinoController)
try:
    from config import ARDUINO_BAUD, ARDUINO_PORT
except ImportError:
    try:
        from config import ARDUINO_BAUD
    except Exception:
        ARDUINO_BAUD = 9600
    ARDUINO_PORT = None
except Exception:
    try:
        from config import ARDUINO_BAUD
    except Exception:
        ARDUINO_BAUD = 9600
    ARDUINO_PORT = None

import threading
import time
import sys

# Optional pyserial listing (best-effort)
try:
    from serial.tools import list_ports as _list_ports
except Exception:
    _list_ports = None

# ---- Emotion localization ----
_EMO_MAP = {"happy":"mutluluk","angry":"öfke","sad":"üzgün","surprise":"şaşkınlık","fear":"korku","calm":"huzur","neutral":"nötr","neutrality":"nötr"}
def _localize_emotion(e: str) -> str:
    if not e: return ""
    return _EMO_MAP.get((e or "").strip().lower(), (e or ""))

def _get_default_microphone_id() -> str:
    try:
        default_input = sounddevice.default.device[0]
        if default_input is not None:
            device_info = sounddevice.query_devices(default_input, "input")
            mic_name = device_info.get("name")
            if mic_name:
                return f"mic:{mic_name}"
            return f"mic_index:{default_input}"
    except Exception:
        pass
    return "guest"

def _open_arduino_controller():
    # Try different constructor signatures to be compatible with your current arduino_controller.py
    # Preference order: (port, baud), (baud kw only), (positional), (no args)
    last_err = None
    if ARDUINO_PORT:
        try:
            return ArduinoController(port=ARDUINO_PORT, baud=ARDUINO_BAUD)
        except TypeError as e:
            last_err = e
            # try positional (port, baud)
            try:
                return ArduinoController(ARDUINO_PORT, ARDUINO_BAUD)
            except TypeError as e2:
                last_err = e2
            except Exception as e2:
                last_err = e2
    # no port or unsupported -> try keyword baud
    try:
        return ArduinoController(baud=ARDUINO_BAUD)
    except TypeError as e:
        last_err = e
        # try positional single-arg (baud)
        try:
            return ArduinoController(ARDUINO_BAUD)
        except Exception as e2:
            last_err = e2
    # final fallback: no args
    try:
        return ArduinoController()
    except Exception as e:
        last_err = e
    print("[Arduino] Denenen tüm kurucu imzaları başarısız:", last_err, file=sys.stderr)
    raise last_err


def main():
    # Portları yazdır (mevcutsa)
    try:
        if _list_ports:
            ports = [(p.device, p.description) for p in _list_ports.comports()]
            print("[Arduino] Mevcut portlar:", ports)
    except Exception:
        pass

    arduino = _open_arduino_controller()
    try:
        chosen_port = getattr(arduino, "port", None)
        if chosen_port:
            print(f"[Arduino] Kullanılan port: {chosen_port}")
    except Exception:
        pass

    camera = Camera()

    daily_mood = get_today_mood()
    try:
        current_label = (mood_tracker.get_current_mood().get("mood") or "").lower()
    except Exception:
        current_label = ""
    if daily_mood and daily_mood.lower() not in current_label:
        mood_tracker.update_mood(daily_mood)
    
    otto_system = OttoControlSystem(mood_tracker_module=mood_tracker, arduino_controller=arduino)

    try:
        threading.Thread(target=camera.show_camera_feed, daemon=True).start()
    except Exception:
        try:
            threading.Thread(target=camera.run_camera, daemon=True).start()
        except Exception:
            pass

    try:
        speak("Bir saniye, yüzünü tanımaya çalışıyorum...")
        face_frame = camera.capture_frame()
        name = recognize_face(face_frame)
        
        voice_id = name if name else _get_default_microphone_id()
        stored_name = get_user_name_by_voice_id(voice_id) if voice_id else None
        is_new_user = stored_name is None

        if stored_name:
            name = stored_name

        if name:
            if needs_goal_review(user=name):
                speak("Geçen gün bir hedef koymuştum. İstersen nasıl gittiğini konuşabiliriz.")
                otto_system.process_input(sentiment="mutluluk")
                last_emotion = get_last_emotion_for_user(name)
                if last_emotion:
                    speak(f"{name}... Geçen buluştuğumuzda biraz {last_emotion} hissediyordum. Ama seninle konuşmak iyi gelmişti.")
                else:
                    speak(f"Hoş geldin {name}! Seni hemen tanıdım.")
        else:
            speak("Seni daha önce görmemiş gibiyim. Tanışalım mı?")
            otto_system.process_input(sentiment="mutluluk")
            name_input = listen_and_recognize()
            if name_input:
                name = name_input.strip().split(" ")[0]
                voice_id = name or voice_id
                is_new_user = True
                registered = register_new_face(name, face_frame)
                if registered:
                    speak(f"Memnun oldum {name}, yüzünü hafızama kaydettim.")
                else:
                    speak("Yüzünü algılayamadım ama ismini hatırlayacağım.")
            else:
                is_new_user = False

        if not name:
            name = "Misafir"
            is_new_user = False
        if is_new_user and voice_id and name != "Misafir":
            register_new_user(voice_id, name)

        mood = mood_tracker.get_current_mood()
        memory = get_memory_about(name)
        if daily_mood:
            if name == "Meva":
                speak(f"Meva... en yakın arkadaşım. Bugün kendimi {daily_mood} hissediyorum.")
            else:
                speak(f"{name}, bugün kendimi {daily_mood} hissediyorum.")
        elif name == "Meva":
            speak(f"Meva... en yakın arkadaşım. Bugün biraz {mood.get('mood','nötr')} hissediyorum.")
        if memory:
            speak(f"Bu arada {name}, hatırlıyor musun? {memory}")

        camera_frame_counter = 0
        while True:
            command = listen_and_recognize()
            if not command:
                continue

            lower_cmd = command.lower()

            # behavioral toggles
            if "neden böyle hissediyorum" in lower_cmd or "son zamanlarda nasılım" in lower_cmd:
                continue
            if "artık ciddi konuş" in lower_cmd or "resmi ol" in lower_cmd:
                set_user_mode(voice_id, "resmi"); speak("Tamam. Bundan sonra daha ciddi konuşacağım."); continue
            if "daha komik ol" in lower_cmd or "komik cevaplar" in lower_cmd:
                set_user_mode(voice_id, "komik"); speak("Haha! Harika! Bundan sonra daha komik olacağım."); continue
            if "robot gibi" in lower_cmd or "robotik konuş" in lower_cmd:
                set_user_mode(voice_id, "robotik"); speak("Mod ayarlandı. Artık robot gibi konuşuyorum."); continue
            if "samimi ol" in lower_cmd or "arkadaşça konuş" in lower_cmd:
                set_user_mode(voice_id, "samimi"); speak("Peki! Daha içten ve arkadaşça konuşacağım."); continue
            if "üzgünsem moral ver" in lower_cmd:
                added = add_behavior_rule(voice_id, "when_user_is", "üzgün")
                speak("Anlaşıldı. Üzgün olduğunda seni neşelendirmeye çalışacağım." if added else "Zaten böyle bir kuralım vardı.")
                continue

            # journal & memory
            if "bugün nasıldım" in lower_cmd:
                speak(summarize_today(user=name)); continue
            if "önemli anılar" in lower_cmd:
                memories = get_important_memories(user=name)
                if memories:
                    speak("İşte en önemli anılarım:"); [speak(m) for m in memories]
                else:
                    speak("Henüz önemli bir anım yok."); continue
            if "günlüğünü oku" in lower_cmd:
                entries = get_last_entries(user=name)
                if entries:
                    speak("İşte son günlük kayıtlarım:"); [speak(e) for e in entries]
                else:
                    speak("Günlükte kayıt bulunamadı."); continue
            if "en mutlu anın" in lower_cmd:
                best = get_best_memory(user=name)
                speak(f"En mutlu anım: {best}" if best else "Henüz en mutlu anımı bulamadım."); continue
            if "meva hakkında" in lower_cmd:
                entries = get_entries_about("Meva")
                if entries:
                    speak("Meva hakkında şunları hatırlıyorum:"); [speak(e) for e in entries[:3]]
                else:
                    speak("Meva hakkında bir şey yazmamışım."); continue

            # generate response & action
            mode = get_user_mode(voice_id)
            response = get_ai_response(command, mood, name, mode)
            sentiment_raw = get_sentiment(response)
            sentiment = _localize_emotion(sentiment_raw)
            mood_tracker.update_mood(sentiment)
            mood = mood_tracker.get_current_mood()
            speak(response, emotion=sentiment)

            add_memory_about(name, f"{name} bana '{command}' dediğimde şöyle cevap verdim: '{response}'")
            write_to_journal(name, f"{name} bana '{command}' dediğimde ben şöyle cevap verdim: '{response}'")

            otto_system.process_input(sentiment=sentiment, user_command=command)

            camera_frame_counter += 1
            if camera_frame_counter >= 5:
                frame = camera.capture_frame()
                face_emotion_raw = analyze_face_emotion(frame)
                face_emotion = _localize_emotion(face_emotion_raw)
                otto_system.process_input(sentiment=face_emotion)
                camera_frame_counter = 0

            time.sleep(1)

    finally:
        try:
            camera.release()
        except Exception:
            pass
        try:
            arduino.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
