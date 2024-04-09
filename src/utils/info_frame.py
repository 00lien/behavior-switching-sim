
import cv2
import numpy as np
import threading

class InfoPanel(object):

    def __init__(self, size=(640, 480)):
        self.imstack = None
        self.text_panel = None
        self.last_text_state = (10, 10)
        self.size = size

    def add_stack(self,image):
        resized = cv2.resize(image.copy(), (360, 240), interpolation= cv2.INTER_LINEAR)
        self.imstack = np.hstack((
            self.imstack, 
            resized
        )) if self.imstack is not None else resized

    def generate_empty_image(self):
        return np.ones(shape=(self.size[0], self.size[1],3), dtype=np.uint8)

    def put_text(self, text):
        if(self.text_panel is None):
            self.text_panel = self.generate_empty_image()

        cv2.putText(self.text_panel, text=text, org=self.last_text_state, fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL, fontScale=1, color=(255, 255, 255),thickness=2)
        self.last_text_state = (self.last_text_state[0], self.last_text_state[1]+30)

    def get_panel(self):
        return self.text_panel

    def get_image_stack(self):
        return self.imstack

    def reset_image_stack(self):
        self.imstack = None
        self.text_panel = None
        self.last_text_state = (70, 70)
        
