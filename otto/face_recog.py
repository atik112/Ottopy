
import face_recognition
import cv2
import os
import pickle

DATA_PATH = 'data/face_data.pkl'

def load_known_faces():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "rb") as f:
            return pickle.load(f)
    return {}

def save_known_faces(data):
    with open(DATA_PATH, "wb") as f:
        pickle.dump(data, f)

def register_new_face(name, image):
    known_faces = load_known_faces()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb_image)

    if encodings:
        known_faces[name] = encodings[0]
        save_known_faces(known_faces)
        return True
    return False

def recognize_face(image):
    known_faces = load_known_faces()
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    unknown_encodings = face_recognition.face_encodings(rgb_image)

    if not unknown_encodings:
        return None

    unknown_encoding = unknown_encodings[0]
    for name, known_encoding in known_faces.items():
        match = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.5)
        if match[0]:
            return name
    return None
