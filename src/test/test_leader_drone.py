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


def main():

    init_pad_positions = {
        1: (0,0,0),
        2: (-0.6, 0.6, 0),
        3: (0, 0, 0)
    }

    # plot = NBPlot(min_v=-5, max_v=5, figure_width=12)
    # plot.plot(None)
    
    #initiate ground controller
    controller = Controller()

    #leader drone
    leader_drone = Factory.buildServerDrone()
    controller.register_drone(leader_drone)

    print("Registered Drones are ->")
    controller.print_registered_drones()

    #c.add_listener('Key.space', lambda : controller.swarm_land_emergency())

    #connect to drones
    controller.swarm_connect_all()
    controller.swarm_wait_for_connect_ok()

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

    while(1):
        a = input("enter x,y =")

        if(a == 'q'):
            break

        a = a.split(',')
        print('---------------------------------')
        print('current position', leader_drone.get_globle_position_vector())
        leader_drone.go_to_position_in_meters(int(a[0]), int(a[1]))
        leader_drone.wait_for_async_control_command()
        leader_drone.wait_until_drone_stops()
        print(leader_drone.get_position_ref_to_grid(), leader_drone.get_globle_position_vector())
        

    # leader_drone.go_to_position_ref_to_grid(1,0)
    # leader_drone.wait_for_async_control_command()
    # leader_drone.wait_until_drone_stops()
    # print(leader_drone.get_globle_position_vector())

    # leader_drone.go_to_position_ref_to_grid(-1,0)
    # leader_drone.wait_for_async_control_command()
    # leader_drone.wait_until_drone_stops()
    # print(leader_drone.get_globle_position_vector())

    # leader_drone.go_to_command(2,1)
    # leader_drone.wait_for_async_control_command()

    # leader_drone.go_to_command(2,-1)
    # leader_drone.wait_for_async_control_command()

    # leader_drone.go_to_command(1,-1)
    # leader_drone.wait_for_async_control_command()

    # leader_drone.go_to_command(0,0)
    # leader_drone.wait_for_async_control_command()




    # leader_drone.send_command(COMMANDS.go_curve_relevent_to_global_3D((1.5, 1.0, 2.0), leader_drone.get_globle_position_vector(), 60))
    # leader_drone.wait_for_async_control_command()

    print('Land -------------------')
    controller.swarm_land_all()
    controller.swarm_wait_for_control_ok()

    controller.deregister_all_drones()
    print(controller.get_registered_drones())
    

if __name__ == '__main__':
    main()