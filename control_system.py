
# control_system.py


# --- Arduino komut çevirici (Python -> Arduino seri) ---
def translate_for_arduino(cmd: str) -> str:
    table = {
        "SWING": "dance",
        "TIPTOE_SWING": "moonwalker",
        "SHAKE_LEG": "shake_leg",
        "CRUSAITO": "moonwalker",
        "BEND": "bend",
        "JUMP": "jump",
        "SIT": "ottosad",
        # Küçük harfli komutlar doğrudan geçer
        "dance": "dance",
        "moonwalker": "moonwalker",
        "shake_leg": "shake_leg",
        "bend": "bend",
        "jump": "jump",
        "ottosad": "ottosad",
        "walk_forward": "walk_forward",
        "walk_backward": "walk_backward",
        "turn_left": "turn_left",
        "turn_right": "turn_right",
    }
    return table.get((cmd or "").strip(), (cmd or "").strip())
# Eşleme fonksiyonları

def map_emotion_to_command(sentiment: str) -> str:
    emotion_map = {
        "mutluluk": "SWING",
        "heyecan": "JUMP",
        "huzur": "BEND",
        "şaşkınlık": "TIPTOE_SWING",
        "öfke": "SHAKE_LEG",
        "korku": "CRUSAITO",
        "üzgün": "SIT",
        "hayal kırıklığı": "SIT"
    }
    return emotion_map.get(sentiment.lower(), "NEUTRAL")


def map_text_command_to_otto_action(user_text: str) -> str:
    user_text = user_text.lower()
    if "dans" in user_text:
        return "MOONWALKER"
    elif "selam" in user_text or "el salla" in user_text:
        return "FLAPPING"
    elif "otur" in user_text:
        return "SIT"
    elif "zıpla" in user_text:
        return "JUMP"
    elif "sağa dön" in user_text:
        return "TURN_RIGHT"
    elif "sola dön" in user_text:
        return "TURN_LEFT"
    elif "yürü" in user_text:
        return "WALK"
    elif "eğil" in user_text:
        return "BEND"
    else:
        return "NEUTRAL"


# Duygu köprüsü
class RealisticOttoEmotionBridge:
    def __init__(self, mood_tracker_module, arduino_controller):
        self.mood_tracker = mood_tracker_module
        self.arduino = arduino_controller

    def process_emotion(self, sentiment):
        self.mood_tracker.update_mood(sentiment)
        score = self.mood_tracker.get_current_mood().get("score", 0)
        print(f"[Mood] Güncel skor: {score}")

        command = map_emotion_to_command(sentiment)
        converted_command = translate_for_arduino(command)
        print(f"[Otto] Duyguya göre komut: {command} -> Arduino: {converted_command}")
        self.arduino.send_data(converted_command)


# Komut köprüsü
class UserCommandBridge:
    def __init__(self, arduino_controller):
        self.arduino = arduino_controller

    def process_user_command(self, user_text):
        command = map_text_command_to_otto_action(user_text)
        converted_command = translate_for_arduino(command)
        print(f"[Kullanıcı Komutu] '{user_text}' -> Otto komutu: {command} -> Arduino: {converted_command}")
        self.arduino.send_data(converted_command)


# Ana kontrol sistemi
class OttoControlSystem:
    def __init__(self, mood_tracker_module, arduino_controller):
        self.emotion_bridge = RealisticOttoEmotionBridge(mood_tracker_module, arduino_controller)
        self.command_bridge = UserCommandBridge(arduino_controller)

    def process_input(self, sentiment=None, user_command=None):
        if sentiment:
            print(f"\n[INPUT] Duygu algılandı: {sentiment}")
            self.emotion_bridge.process_emotion(sentiment)

        if user_command:
            print(f"\n[INPUT] Kullanıcı komutu alındı: {user_command}")
            self.command_bridge.process_user_command(user_command)
