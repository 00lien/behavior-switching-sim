import sys
import time
sys.path.append('C:/Users/soc/Kolitha/Projects/Tello-Object-Tracking')
sys.path.append('/Users/kolithawarnakulasooriya/Projects/Tello_Scripts')

from lib.soc.drone_factory.factory import Factory
from lib.soc.drone_factory.commands import COMMANDS
from lib.soc.utils.state import State
from lib.soc.ground_station.controller import Controller
from lib.soc.view.drone_trajectory import NBPlot
from lib.soc.utils.keyboard_controller import KeyBoradController

c = KeyBoradController()

def main():

    #initiate ground controller
    controller = Controller()

    #leader drone
    drone = Factory.buildCommonDrone(ip="192.168.10.1")
    controller.register_drone(drone)

    print("Registered Drones are ->")
    controller.print_registered_drones()

    #connect to drones
    controller.swarm_connect_all()
    controller.swarm_wait_for_connect_ok()

    try:
        while(True):
            controller.print_states()
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    controller.deregister_all_drones()
    print(controller.get_registered_drones())
    

if __name__ == '__main__':
    main()