
import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import time
from voice.text_to_speech import speak
from voice.speech_recognition import listen_and_recognize
from otto.face_recog import recognize_face, register_new_face
import threading

class Camera:
    def __init__(self):
        self.model = YOLO("yolov8n.pt")
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": (640, 480)})
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(1)

        self.last_seen = {}
        self.known_faces = set()
        self.ready_event = threading.Event()

    def show_camera_feed(self):
        cv2.namedWindow("Otto'nun Kamerası", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Otto'nun Kamerası", 640, 480)
        while True:
            frame = self.capture_frame()
            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            cv2.imshow("Otto'nun Kamerası", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

    def capture_frame(self):
        frame = self.picam2.capture_array()
        if frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame
