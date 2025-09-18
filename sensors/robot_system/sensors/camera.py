import cv2
import time
import threading
from ultralytics import YOLO
from config import CAMERA_INDEX
from voice.text_to_speech import speak
from voice.speech_recognition import listen_and_recognize
from otto.face_recog import recognize_face, register_new_face

try:
    from picamera2 import Picamera2
    _HAS_PICAMERA2 = True
except Exception:
    Picamera2 = None
    _HAS_PICAMERA2 = False

class Camera:
    _lock = threading.Lock()
    _singleton_started = False

    def __init__(self):
        self.model = YOLO("yolov8n.pt")
        self.use_picam2 = False
        self.picam2 = None
        self.cap = None

        # Ensure only one instance actively talks to camera
        with Camera._lock:
            if _HAS_PICAMERA2 and not Camera._singleton_started:
                try:
                    self.picam2 = Picamera2()
                    cfg = self.picam2.create_preview_configuration(main={"size": (640, 480)})
                    self.picam2.configure(cfg)
                    self.picam2.start()
                    self.use_picam2 = True
                    Camera._singleton_started = True
                except Exception as e:
                    # Fallback to OpenCV capture
                    self.picam2 = None
                    self.use_picam2 = False

            if not self.use_picam2:
                self.cap = cv2.VideoCapture(CAMERA_INDEX)
                # small warmup
                time.sleep(0.2)
                if not self.cap.isOpened():
                    raise RuntimeError("Kamera açılamadı: Picamera2 başarısız ve OpenCV de bağlanamadı.")

    def release(self):
        with Camera._lock:
            if self.use_picam2 and self.picam2 is not None:
                try:
                    self.picam2.stop()
                except Exception:
                    pass
                try:
                    self.picam2.close()
                except Exception:
                    pass
                Camera._singleton_started = False
                self.picam2 = None
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None

    def capture_frame(self):
        if self.use_picam2 and self.picam2 is not None:
            frame = self.picam2.capture_array()
            if frame is None:
                raise RuntimeError("Picamera2 frame alamadı.")
            if frame.ndim == 3 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame
        else:
            ok, frame = self.cap.read() if self.cap is not None else (False, None)
            if not ok or frame is None:
                raise RuntimeError("OpenCV frame alınamadı.")
            if frame.ndim == 3 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            return frame

    # Eski arayüzle uyumluluk için
    def run_camera(self):
        while True:
            frame = self.capture_frame()
            cv2.imshow("Otto'nun Kamerası", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
        self.release()
