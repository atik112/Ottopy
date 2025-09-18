from deepface import DeepFace
import cv2

def analyze_face_emotion(image):
    try:
        result = DeepFace.analyze(image, actions=["emotion"], enforce_detection=False)
        emotion = result[0]["dominant_emotion"]
        return emotion
    except Exception as e:
        print(f"Yüz analizi hatası: {e}")
        return "bilinmiyor"
