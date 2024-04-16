import sys
import time
sys.path.append('C:/Users/User/Desktop/Orion/Tello/Tello-Object-Tracking')
from lib.soc.drone_factory.factory import Factory
from lib.soc.drone_factory.commands import COMMANDS
from lib.soc.utils.state import State
from lib.soc.ground_station.controller import Controller

def main():

    init_pad_positions = {
        1: (0,0,0),
        2: (-0.6,0.6,0),
        3: (-0.6, -0.6,0)
    }

    #ground controller
    controller = Controller()

    #leader drone
    leader_drone = Factory.buildServerDrone()
    controller.register_drone(leader_drone)

    left_drone = Factory.buildCommonDrone(ip="192.168.0.195")
    controller.register_drone(left_drone)

    right_drone = Factory.buildCommonDrone(ip="192.168.0.198")
    controller.register_drone(right_drone)

    #connect 
    controller.swarm_connect_all()
    controller.swarm_wait_for_connect_ok()

    #takeoff
    controller.swarm_takeoff_all()
    controller.swarm_wait_for_control_ok()

    time.sleep(6)

    controller.swarm_command_for_all(COMMANDS.move_up(30))
    controller.swarm_wait_for_control_ok()

    time.sleep(3)

    leader_drone.send_command(command=COMMANDS.move_forward(120))
    left_drone.send_command(command=COMMANDS.move_right(120))
    right_drone.send_command(command=COMMANDS.go(-140, 120, 0, 80))

    time.sleep(6)

    leader_drone.send_command(command=COMMANDS.move_forward(170))
    left_drone.send_command(command=COMMANDS.move_forward(200))
    right_drone.send_command(command=COMMANDS.move_forward(240))

    time.sleep(6)

    left_drone.send_command(command=COMMANDS.move_left(120))
    right_drone.send_command(command=COMMANDS.go(90, -120, 0, 80))

    time.sleep(6)
    #land
    controller.swarm_land_all()
    controller.swarm_wait_for_control_ok()
    
    #dereg
    controller.deregister_all_drones()

if __name__ == '__main__':
    main()
