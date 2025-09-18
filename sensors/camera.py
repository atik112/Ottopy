import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
import time
from voice.text_to_speech import speak
from voice.speech_recognition import listen_and_recognize
from otto.face_recog import recognize_face, register_new_face
from ai.face_recognizer import FaceRecognizer
import threading

class Camera:
    def __init__(self):
        self.model = YOLO("yolov8n.pt")
        self.face_recognizer = FaceRecognizer()
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": (640, 480)})
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(1)

        self.last_seen = {}
        self.known_faces = set()
        self.ready_event = threading.Event()
        self.last_raw_frame = None
        self.last_processed_frame = None

    def show_camera_feed(self):
        cv2.namedWindow("Otto'nun Kamerası", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Otto'nun Kamerası", 640, 480)
        while True:
            frame = self.capture_frame()
            if frame is None:
                continue
            if frame.ndim == 3 and frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            cv2.imshow("Otto'nun Kamerası", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

    def process_frame(self, frame):
        if frame is None:
            return None

        if frame.ndim == 3 and frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        processed_frame = frame.copy()

        try:
            results = self.model(processed_frame, verbose=False)
        except TypeError:
            results = self.model(processed_frame)

        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                xyxy = box.xyxy[0].tolist()
                x1, y1, x2, y2 = map(int, xyxy)
                conf = float(box.conf[0]) if getattr(box, "conf", None) is not None else 0.0
                cls_id = int(box.cls[0]) if getattr(box, "cls", None) is not None else None
                label_map = getattr(result, "names", None) or getattr(self.model, "names", {})
                label = label_map.get(cls_id, str(cls_id) if cls_id is not None else "Nesne")
                text = f"{label} {conf:.2f}"
                cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                text_origin_y = y1 - 10 if y1 - 10 > 10 else y1 + 20
                cv2.putText(
                    processed_frame,
                    text,
                    (x1, text_origin_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 0, 0),
                    2,
                )

        face_locations, names = self.face_recognizer.recognize_faces(frame)
        if face_locations:
            self.last_raw_frame = frame.copy()
        processed_frame = self.face_recognizer.draw_faces(processed_frame, face_locations, names)

        if processed_frame is not None:
            self.last_processed_frame = processed_frame.copy()

        return processed_frame

    def capture_frame(self):
        frame = self.picam2.capture_array()
        if frame is not None and frame.ndim == 3 and frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        self.last_raw_frame = frame.copy() if frame is not None else None
        processed = self.process_frame(frame)
        return processed
