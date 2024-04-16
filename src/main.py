import sys
sys.path.append('C:/Users/User/Desktop/Orion/Tello/Tello-Object-Tracking')
## tello scripts ? 

import numpy as np
import cv2
from ui.dashboard import Dashboard

class Main(object):
    def __init__(self) -> None:
        self.ui = Dashboard()
        self.ui.mainloop()

if __name__ == '__main__':
    Main()