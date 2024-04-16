
import cv2
import sys
import time
import os
from pubsub import pub
sys.path.append('C:/Users/soc/Kolitha/Projects/Tello-Object-Tracking')
sys.path.append('/Users/kolithawarnakulasooriya/Projects/Tello_Scripts')

from lib.soc.drone_factory.factory import Factory, Drone
from lib.soc.drone_factory.commands import COMMANDS
from lib.soc.ground_station.controller import Controller
from lib.svm.pose_detector import PoseDetector
import pickle

def main():

    print('Start')

    controller = Controller()
    drone:Drone = Factory.buildServerDrone()
    controller.register_drone(drone)
    
    drone.connect_sync()
    print("connected")
    
    fr = drone.set_steam_on()

    drone.take_off()
    drone.wait_for_async_control_command()

    drone.send_command(COMMANDS.move_up(80))

    timeout = time.process_time() + 5
    t1 = time.process_time() + 1

    while(True):
        r, image = fr.get_frame()
        if r:
            cv2.imshow('original', image)

            if time.process_time() >= timeout:
                drone.send_command(COMMANDS.keepalive)
                timeout = time.process_time() + 1
                cv2.imwrite(f"assets/{time.time()}.jpg", image)

        if cv2.waitKey(1) == ord('q'):
            drone.land()
            break

if __name__ == '__main__':
    main()
    