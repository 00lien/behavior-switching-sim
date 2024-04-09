import cv2
import threading
import time
from pubsub import pub
from ..constants import FRAME_GRAB_TIMEOUT, MAIN_CAMERA_FRAME

class BackgroundFrameRead:
    def __init__(self, address):
        self.cap = cv2.VideoCapture(address)
        self.frame = None

        if not self.cap.isOpened():
            self.cap.open(address)

        start = time.time()
        while time.time() - start < FRAME_GRAB_TIMEOUT:
            self.grabbed, self.frame = self.cap.read()
            time.sleep(0.05)
            if self.frame is not None:
                break
        if not self.grabbed or self.frame is None:
            raise Exception('Failed to grab first frame from video stream')

        self.stopped = False
        self.worker = threading.Thread(target=self.update_frame, args=(), daemon=True)

    def start(self):
        self.worker.start()

    def update_frame(self):
        while not self.stopped:
            if not self.grabbed or not self.cap.isOpened():
                self.stop()
            else:
                self.grabbed, self.frame = self.cap.read()
                if self.frame is not None:
                    pub.sendMessage(MAIN_CAMERA_FRAME, data=self.frame)
        self.cap.release()

    def get_frame(self):
        if self.frame is None:
            return (False, None)
        else:
            return(True, self.frame)

    def stop(self):
        self.stopped = True

    @staticmethod
    def get_udp_address(ip, port):
        return "udp://@{}:{}".format(ip, port)
       