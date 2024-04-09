import sys
import time
import math
import argparse
sys.path.append('C:/Users/soc/Kolitha/Projects/Tello-Object-Tracking')
sys.path.append('/Users/kolithawarnakulasooriya/Projects/Tello_Scripts')

from lib.soc.drone_factory.factory import Factory
from lib.soc.drone_factory.commands import COMMANDS
from lib.soc.utils.logger import init_logging
from lib.soc.ground_station.controller import Controller
from lib.soc.view.drone_trajectory import NBPlot
from lib.soc.utils.keyboard_controller import KeyBoradController

# 0TQZK68CNT20XP 1.0 co eff

c = KeyBoradController()

def main(ip:str):

    init_logging(False)

    f = open('pattern_test_{}.txt'.format(ip),'wb')
    
    init_pad_positions = {
        1: (0,0,0)
    }
    
    #initiate ground controller
    controller = Controller()

    c.add_listener('Key.space', lambda x: controller.swarm_land_all())

    #leader drone
    leader_drone = Factory.buildCommonDrone(ip)
    controller.register_drone(leader_drone)

    print("Registered Drones are ->")
    controller.print_registered_drones()

    #connect to drones
    controller.swarm_connect_all()
    controller.swarm_wait_for_connect_ok()

    sn = leader_drone.get_sn()
    f.write(f"Serial Number: {sn}\n".encode())
    print(f"Serial Number: {sn}")

    controller.swarm_command_for_all(COMMANDS.enable_mission_pad)
    controller.swarm_wait_for_control_ok()

    print("Get mpads before takeoff")
    controller.print_registered_drones()

    print('take_off -------------------')
    controller.swarm_takeoff_all()
    controller.swarm_wait_for_control_ok()

    print("Mission Pad Info after take off...")
    controller.swarm_localize_through_mpads(init_pad_positions)
    print(leader_drone.get_position_ref_to_grid(), leader_drone.get_globle_position_vector())

    controller.correct_drone_angles()
    controller.swarm_wait_for_control_ok()

    locs = [
        (4,0),
        (0,0),
        (-4,0),
        (0,0),
        (0,4),
        (0,0),
        (0,-4),
        (0,0), 
        # (1,0),
        # (-1,0),
        # (0,1),
        # (0,-1),
        # (0,0),
        # (1,1),
        # (0,0),
        # (-1,-1),
        # (0,0),
        # (1,-1),
        # (0,0),
        # (-1,1),
        # (0,0),

        # positives
        # (1,1),
        # (1,-1),
        # (2,0),
        # (1,1),
        # (0,0),

        # positives x
        #(2,2),
        # (2,-1),
        # (0,0),
        # (1,0),
        # (0,2),
        # (0,0)
        
    ]

    print("PSI", leader_drone.psi)
    for a in locs:
        p = leader_drone.get_globle_position_vector()
        leader_drone.go_to_position_in_meters(a[0], a[1])
        leader_drone.wait_for_async_control_command()
        leader_drone.wait_until_drone_stops()
        p1 = leader_drone.get_globle_position_vector()
        t = f"[{a}] | x_d={round(p1[0]-p[0],3)} y_d={round(p1[1]-p[1],3)}, err={round(math.sqrt((p1[1]-p[1])**2 + (p1[0]-p[0])**2),3)}, x0 ={round(p[0], 3)} x1={round(p1[0], 3)} y0={round(p[1], 3)} y1={round(p1[0], 3)} \n"
        print(t)
        f.write(t.encode())

    print('Land -------------------')
    controller.swarm_land_all()
    controller.swarm_wait_for_control_ok()

    controller.deregister_all_drones()
    print(controller.get_registered_drones())
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser( prog='Test Drones IMU')
    parser.add_argument('--ip', type=str, help='enter IP')

    main(parser.parse_args().ip)