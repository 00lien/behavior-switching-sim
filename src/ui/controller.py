from utils.configurations import Configs
import pickle
import os
import threading, time
import cv2
from lib.soc.ground_station.controller import Controller, COMMANDS, Drone
from lib.soc.drone_factory.factory import Factory
from lib.soc.utils.keyboard_controller import KeyBoradController
from lib.svm.pose_detector import PoseDetector
from lib.soc.utils.commons import calc_approximate_distance_to_object_by_avg_human_height, to_meters, calc_approximate_x_y_in_mms
from pubsub import pub

class Manager(object):

    def __init__(self, configs:Configs) -> None:

        self.init_pad_positions =  {
            1: (0,0,0),
            2: (-0.6, -1.2, 0),
            3: (-0.6, 1.2, 0),
            8: (-1.2, 0.6, 0),
            5: (-1.2, -0.6, 0)
        }
        self.mapped_wolfs = configs.get_main_json('mapped_wolfs')
        self.model = pickle.load(open(os.path.join(os.getcwd(), 'assets/model.sav'), 'rb'))
        self.kc = KeyBoradController()
        self.detector = PoseDetector()

        #wolfs
        self.alpha_male = None
        self.beta_left = None
        self.beta_right = None
        self.delta_left = None
        self.delta_right = None

        self.stream = None

        self.del_state_value = 2

        #initiate ground controller
        self.ground_controller = Controller()

        self.kc.add_listener('Key.space', lambda _: self.ground_controller.swarm_land_all())
        self.kc.add_listener('Key.esc', lambda _: exit())
        self.kc.add_listener('q', lambda _: self.ground_controller.swarm_land_emergency())

        self.keep_alive_thread = threading.Thread(target=self.__keep_alive, daemon=True)
        self.is_mission_start = False

        self.is_armed = False

    def __keep_alive(self):
        timeout = time.process_time() + 8
        while(True):
            if time.process_time() >= timeout:
                self.ground_controller.swarm_command_for_all(COMMANDS.keepalive)
                timeout = time.process_time() + 5
            time.sleep(0.5)

    def convert_to_pad_obg(self, obj):
        c_obj = {}
        
        for i in dict(obj).keys():
            c_obj[int(i)]= tuple(map(int, map(float, obj[i].split(', '))))

        return c_obj
    
    def stream_on(self):
        self.stream = self.alpha_male.set_steam_on()

    def stream_off(self):
        self.stream = self.alpha_male.set_steam_off()

    def register_drones(self, ips: list):
        self.ground_controller.deregister_all_drones()

        self.alpha_male = Factory.buildServerDrone()
        self.alpha_male.additional_state['is_deployed'] = False
        self.alpha_male.additional_state['last_location'] = (0,0,0)

        self.ground_controller.register_drone(self.alpha_male)
        #initiate wolfs
        for ip in ips:
            self.ground_controller.register_drone(Factory.buildCommonDrone(ip))

    def connect_all(self):
        
        #connect all drones
        self.ground_controller.swarm_connect_all()
        self.ground_controller.swarm_wait_for_connect_ok()

        if not self.keep_alive_thread.is_alive():
            self.keep_alive_thread.start()

    def arm_and_takeoff(self):
            self.is_armed = True
            self.ground_controller.swarm_command_for_all(COMMANDS.enable_mission_pad)
            self.ground_controller.swarm_wait_for_control_ok()

            self.ground_controller.swarm_takeoff_all()
            self.ground_controller.swarm_wait_for_control_ok()

            self.ground_controller.swarm_localize_through_mpads(self.init_pad_positions)

            # update wolf parts
            for drone in self.ground_controller.get_registered_drones().values():
                id = drone.get_state().get_mission_pad_id()
                if id == int(self.mapped_wolfs["ALPHA"]):
                    self.alpha_male = drone
                    self.alpha_male.additional_state['is_deployed'] = False
                    self.alpha_male.additional_state['last_location'] = (0,0,0)
                    print(f"Alha Male Drone: {self.alpha_male.get_ip()}")
                elif id == int(self.mapped_wolfs["BETA_LEFT"]):
                    self.beta_left = drone
                    self.beta_left.additional_state['is_deployed'] = False
                    self.beta_left.additional_state['last_location'] = (0,0,0)
                    print(f"Beta support left drone: {self.beta_left.get_ip()}")
                elif id == int(self.mapped_wolfs["BETA_RIGHT"]):
                    self.beta_right = drone
                    self.beta_right.additional_state['is_deployed'] = False
                    self.beta_right.additional_state['last_location'] = (0,0,0)
                    print(f"Beta support right drone: {self.beta_right.get_ip()}")
                elif id == int(self.mapped_wolfs["DELTA_LEFT"]):
                    self.delta_left = drone
                    self.delta_left.additional_state['is_deployed'] = False
                    self.delta_left.additional_state['last_location'] = (0,0,0)
                    print(f"Delta support right drone: {self.delta_left.get_ip()}")
                elif id == int(self.mapped_wolfs["DELTA_RIGHT"]):
                    self.delta_right= drone
                    self.delta_right.additional_state['is_deployed'] = False
                    self.delta_right.additional_state['last_location'] = (0,0,0)
                    print(f"Delta support right drone: {self.delta_right.get_ip()}")

            self.ground_controller.swarm_print_global_localization()

            self.ground_controller.correct_drone_angles()
            self.ground_controller.swarm_wait_for_control_ok()

    def land(self):
        #land all drones
        self.ground_controller.swarm_come_back_init_positions()
        self.ground_controller.swarm_wait_for_control_ok()

        self.ground_controller.swarm_land_all()
        self.ground_controller.swarm_wait_for_connect_ok()
        self.is_mission_start = False
        self.is_armed = False

    def emland(self):
        #connect all drones
        self.ground_controller.swarm_land_emergency()
        self.ground_controller.swarm_wait_for_connect_ok()
        self.is_mission_start = False
        self.is_armed = False

    def mission_start(self):
        if not self.is_mission_start:
            self.is_mission_start = True
            threading.Thread(target=self.play_mission, daemon=True).start()

    def get_frame(self):
        ret, image = self.stream.get_frame()
        if ret:
            response = self.detector.detect(image)
            prepaire_image = image.copy()
            pose_image = image.copy()
            
            if response is not None:
                feature_array = self.detector.get_feature_array()
                predicted = self.model.predict([feature_array])
                if predicted is not None:
                    state = predicted[0]
                    pose_image = self.detector.draw()
                    ((x1, y1), (x2, y2),(xc, yc),(xr, yr)) = self.detector.get_countours()
                    if state == 1:
                        cv2.rectangle(prepaire_image, (x1, y1), (x2, y2), (0,0,255), 2)
                        cv2.drawMarker(prepaire_image, (xc, yc), (255, 255, 0), cv2.MARKER_CROSS, 30, 4)
                        cv2.drawMarker(prepaire_image, (xr, yr), (0, 255, 255), cv2.MARKER_CROSS, 30, 4)
                        dist_pixel = abs(y1-y2)
                        approximately_distance = calc_approximate_distance_to_object_by_avg_human_height(dist_pixel)
                        (a_x, a_y) = calc_approximate_x_y_in_mms(xc, yc, 0.0002645833)

                        cv2.putText(prepaire_image, f"d={to_meters(approximately_distance)}, x={to_meters(a_x)}, y={to_meters(a_y)}",(50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3, cv2.LINE_AA)
                        #calculate estimated location
                        return ret, state, prepaire_image, (self.alpha_male.x + to_meters(approximately_distance), self.alpha_male.y, self.alpha_male.z), pose_image

                    else:
                        cv2.rectangle(prepaire_image, (x1, y1), (x2, y2), (0,255,0), 2)
                        return ret, state, prepaire_image, None, pose_image

        return ret, None, image, None, pose_image

    def deploy_drone(self, drone: Drone, x, y):

        if drone is not None and not drone.is_flying() and not drone.additional_state['is_deployed']:
            print(f"{drone.get_ip()} is deployed...!", x, y)
            drone.additional_state['is_deployed'] = True
            drone.additional_state['last_location'] = drone.get_globle_position_vector()
            drone.go_to_position_in_meters(x, y, 0)

    def fallback_drone(self, drone: Drone):
        if drone is not None and not drone.is_flying() and drone.additional_state['is_deployed']:
            print(f"{drone.get_ip()} is fallen back...!")
            (x, y, z) =  drone.additional_state['last_location']
            drone.additional_state['is_deployed'] = False
            drone.go_to_position_in_meters(x, y, 0)

    def play_mission(self):

        self.stream_on()

        if not self.is_armed:
            self.arm_and_takeoff()

        self.ground_controller.swarm_command_for_all(COMMANDS.move_up(80))
        self.ground_controller.swarm_wait_for_control_ok()

        self.alpha_male.send_command(COMMANDS.move_up(25))
        self.alpha_male.wait_for_async_control_command()

        self.ground_controller.swarm_command_for_all(COMMANDS.move_forward(60))
        self.ground_controller.swarm_wait_for_control_ok()
        self.ground_controller.swarm_update_gc(0.6, 0)
        
        
        while(self.is_mission_start):
            ret, state, image, loc, pose_image = self.get_frame()

            if ret:
                pub.sendMessage('original_image', data=image)

                if state is not None:
                    print(self.del_state_value)
                    if state > 0: # here is a threat

                        if self.del_state_value < 65:
                            self.del_state_value += 1
                        
                        if self.del_state_value > 60:
                            if loc is not None:
                                x = loc[0]
                                y = loc[1]
                                self.deploy_drone(self.delta_left, self.beta_left.x - 1.4, y+1.0)
                                self.deploy_drone(self.delta_right, self.beta_right.x - 1.4, y-0.8)
                        elif self.del_state_value > 30:
                            if loc is not None:
                                x = loc[0]
                                y = loc[1]
                                self.deploy_drone(self.beta_left, x-0.8, y+0.5)
                                self.deploy_drone(self.beta_right, x-0.5, y-0.3)
                        else:
                            pass
                    else:
                        if self.del_state_value > 2:
                            self.del_state_value -= 1

                        if self.del_state_value < 10:
                            self.fallback_drone(self.beta_left)
                            self.fallback_drone(self.beta_right)
                        elif self.del_state_value < 35:
                            self.fallback_drone(self.delta_left)
                            self.fallback_drone(self.delta_right)
                        else:
                            pass

        print("Mission End")