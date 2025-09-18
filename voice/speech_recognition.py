import speech_recognition as sr

def listen_and_recognize():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        try:
            print("Dinleniyor...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Sesi işliyorum...")

            command = recognizer.recognize_google(audio, language="tr-TR")
            print("Algılanan komut:", command)
            return command

        except sr.WaitTimeoutError:
            print("Zaman aşımı – ses gelmedi.")
            return None

        except sr.UnknownValueError:
            print("Ses anlaşılamadı.")
            return None

        except sr.RequestError as e:
            print(f"Google API hatası: {e}")
            return None

        except Exception as e:
            print(f"Bilinmeyen hata: {e}")
            return None
