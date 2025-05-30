import cv2
import weakref
import numpy as np
import threading
from time import sleep

class VideoManager():
    def __init__(self, user):
        self.user = weakref.ref(user)
        self.frame = 0

    def _frame_encode(self, frame: np.typing.NDArray[np.uint8]) -> bytes:
        return cv2.imencode('.jpg', frame)[1].tobytes()

    def _frame_decode(self, bytes_frame: bytes) -> np.typing.NDArray[np.uint8]:
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
            self.frame = frame
            bytes_frame = self._frame_encode(frame)
            with self.user().lock:
                if ret:
                    self.user().publisher.send_multipart([b'video', self.user().username.encode('utf-8'), bytes_frame])
            sleep(1/30)

            

    def recieve_video(self, user: str, bytes_frame: bytes):
        cv2.imshow(user, self._frame_decode(bytes_frame))
        cv2.imshow('Voce', self.frame)
        cv2.waitKey(1)




