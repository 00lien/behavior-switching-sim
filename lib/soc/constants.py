import numpy as np
import math

DEFAULT_HOST_IP = ''
DEFAULT_HOST_COMMAND_PORT =  8889
DEFAULT_HOST_STATE_PORT =  8890
DEFAULT_CV_IP = '0.0.0.0'
DEFAULT_CV_PORT = 11111
DEFAULT_BUFFER_SIZE =1024

DEFAULT_DRONE_IP = '192.168.10.1'
MAX_TIME_OUT = 5.0
FRAME_GRAB_TIMEOUT = 3

MIN_BATTERY_AMOUNT = 10

# 1 pixel is mms
FOCUL_LENGTH = 20
# averager height of a person in mms
AVERAGE_HEIGHT_OF_A_PERSON = 1800
FRAME_HEIGHT = 720
FRAME_WIDTH = 960
SENSOR_SIZE = 17

GRID_SIZE=0.6 # meters


MARGINE_FROM_CENTER=(2.5, -1.8, 1.8, -1.5)

# TOPIC
ODO = 'odo'
MAIN_CAMERA_FRAME = 'drone_image'