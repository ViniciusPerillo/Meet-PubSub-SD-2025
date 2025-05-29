import cv2
import weakref
import numpy as np
import threading

class VideoManager():
    def __init__(self, user):
        self.user = weakref.ref(user)
        

    def _frame_encode(frame: np.typing.NDArray[np.uint8]) -> bytes:
        return cv2.imencode('.jpg', frame)[1].tobytes()

    def _frame_decode(bytes_frame: bytes) -> np.typing.NDArray[np.uint8]:
        return cv2.imdecode(np.frombuffer(bytes_frame, np.uint8), cv2.IMREAD_COLOR)

    def setup_video(self):
        self.cam = cv2.VideoCapture(0)
        threading.Thread(target=self.input_callback, daemon=True).start()

    def stop(self):
        self.cam.release()
        cv2.destroyAllWindows()


    def input_callback(self):
        while self.user().on_room:
            ret, frame = self.cam.read()
            bytes_frame = self._frame_encode(frame)
            self.user().publisher.send_multipart([b'video', self.user().username.encode('utf-8'), ])
            self.output_callback('Você', bytes_frame)

    def output_callback(self, user: str, bytes_frame: bytes):
        cv2.imshow(user, self._frame_encode(bytes_frame))




